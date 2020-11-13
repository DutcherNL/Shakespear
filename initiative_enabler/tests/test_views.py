import datetime
from django.test import TestCase, RequestFactory
from django.utils import timezone

from initiative_enabler.views import *
from initiative_enabler.tests import set_up_rsvp, set_up_tech_scores, generate_inquiry_with_score, get_get_request


class QuickTestAdjustmentsMixin:
    def set_rsvp_last_send(self, rsvp=None, now=False, **kwargs):
        """
         Adjusts the last_send_on attribute on the given rsvp
        :param rsvp: The rsvp instance, defaults self.rsvp
        :param now: boolean whether current time should be given otherwise uses rsvp's last_send_on value
        :param kwargs: timedelta kwargs
        :return:
        """
        if rsvp is None:
            rsvp = self.rsvp
        if now:
            last_send_on = timezone.now()
        else:
            last_send_on = rsvp.last_send_on
        if kwargs:
            last_send_on = last_send_on - datetime.timedelta(**kwargs)
        self.rsvp.last_send_on = last_send_on
        self.rsvp.save()
        self.rsvp.refresh_from_db()
        return last_send_on

    def open_collective(self, new_state, collective=None):
        if collective is None:
            collective = self.collective

        collective.is_open = new_state
        collective.save()
        collective.refresh_from_db()


class RSVPViewTestCase(QuickTestAdjustmentsMixin, TestCase):
    def setUp(self):
        # Set up the database
        set_up_rsvp(self)
        self.get_request = RequestFactory().get('/')
        if not hasattr(self.get_request, 'session'):
            self.get_request.session = {}  # Set a dict for the session in case session data is needed at any point
        self.setUp_view()

    def setUp_view(self, url_code=None, with_expired_check=True):
        self.view = CollectiveRSVPView()
        url_code = url_code or self.rsvp.url_code
        if with_expired_check:
            self.view.setup(self.get_request, rsvp_slug=url_code)
        else:
            self.view.setup(self.get_request, collective_id=self.rsvp.collective.id)

    def test_rsvp_view_normal(self):
        """ Tests QuickSendInvitationForm """
        self.assertEqual(self.view.form_class, RSVPAgreeForm)
        self.assertEqual(self.view.template_name, "initiative_enabler/rsvps/rsvp_collective_normal.html")
        self.assertEqual(self.view.rsvp, self.rsvp)
        context = self.view.get_context_data()
        self.assertIn('rsvp', context)
        self.assertEqual(context['rsvp'], self.rsvp)

    def test_rsvp_view_404(self):
        self.setUp_view(url_code='no_match')
        self.assertIsNone(self.view.rsvp)

        response = self.view.dispatch(self.get_request, url_code='no_match')
        self.assertEqual(response.status_code, 404)

    def test_rsvp_view_closed_collective(self):
        self.open_collective(False)
        self.setUp_view()

        self.assertEqual(self.view.rsvp, self.rsvp)
        self.assertEqual(self.view.form_class, RSVPOnClosedForm)
        self.assertEqual(self.view.template_name, "initiative_enabler/rsvps/rsvp_collective_on_closed.html")

    def test_rsvp_view_expired(self):
        self.set_rsvp_last_send(now=True, days=14)
        self.open_collective(False)
        self.setUp_view()

        self.assertEqual(self.view.rsvp, self.rsvp)
        self.assertEqual(self.view.form_class, RSVPRefreshExpirationForm)
        self.assertEqual(self.view.template_name, "initiative_enabler/rsvps/rsvp_collective_expired.html")

        self.get_request.session['inquirer_id'] = self.rsvp.inquirer.id
        self.setUp_view(with_expired_check=False)
        # Expiration is not relevant as the rsvp inquirer has the session currently active
        # However, the form is still closed
        self.assertEqual(self.view.form_class, RSVPOnClosedForm)

        # Assert that the inquirer needs to have an open RSVP in this collective
        self.get_request.session['inquirer_id'] = self.rsvp.inquirer.id + 50
        self.setUp_view(with_expired_check=False)
        self.assertIsNone(self.view.rsvp)

    def test_rsvp_view_already_activated(self):
        self.rsvp.activated = True
        self.rsvp.save()
        self.setUp_view()

        response = self.view.dispatch(self.get_request, url_code='no_match')
        self.assertEqual(response.template_name[0], "initiative_enabler/rsvps/rsvp_collective_already_activated.html")
        self.assertEqual(response.status_code, 410)  # HTTP Gone

        # Ensure that a closed collective does not take priority
        self.open_collective(False)
        self.setUp_view()

        response = self.view.dispatch(self.get_request, url_code='no_match')
        self.assertEqual(response.template_name[0], "initiative_enabler/rsvps/rsvp_collective_already_activated.html")
        self.assertEqual(response.status_code, 410)  # HTTP Gone


class TestActionOverviewView(TestCase):

    def setUp(self):
        self.view = TakeActionOverview()
        self.get_request = get_get_request()
        self.inquirer = Inquirer.objects.create()
        self.inquirer.active_inquiry = Inquiry.objects.create(inquirer=self.inquirer)
        self.inquirer.save()

        self.get_request.session['inquirer_id'] = self.inquirer.id

        self.view.setup(self.get_request)

    def test_get_advised_techs_method(self):
        """ Tests the views get_advised_techs method """
        set_up_tech_scores(self, inquiry=self.inquirer.active_inquiry)

        # Set up a tech improvement that should be ignored as the resulting advise is not present
        TechScoreLink.objects.create(
            score_declaration=ScoringDeclaration.objects.create(name="tech_1_score"),
            technology=Technology.objects.create(name="ignore_this_tech"))
        TechImprovement.objects.create(technology=Technology.objects.get(name="ignore_this_tech"))

        # Test that there are no valid advised tech improvements
        advised_techs = self.view.get_advised_techs()
        self.assertEqual(len(advised_techs), 0)

        # Do use this tech
        TechImprovement.objects.create(technology=self.t1)
        advised_techs = self.view.get_advised_techs()
        self.assertEqual(len(advised_techs), 1)
        self.assertEqual(advised_techs[0], self.t1)

    def test_has_not_interested_collectives_method(self):
        """ Tests the views has_not_interested_collectives method """
        # Note, a tech without any declaration by default is advised

        TechCollectiveInterest.objects.create(
            inquirer=self.inquirer,
            tech_collective=TechCollective.objects.create(technology=Technology.objects.create(name='nn1')),
            is_interested=True)

        self.assertFalse(self.view.has_not_interested_collectives())

        # Test that a uninterested inquirer fails
        TechCollectiveInterest.objects.create(
            inquirer=self.inquirer,
            tech_collective=TechCollective.objects.create(technology=Technology.objects.create(name='nn3')),
            is_interested=False)
        self.assertTrue(self.view.has_not_interested_collectives())

        #
        TechCollectiveInterest.objects.filter(tech_collective__technology__name='nn3').update(is_interested=True)
        self.assertFalse(self.view.has_not_interested_collectives())

        # Test that a non-advised tech is not taken into account
        TechScoreLink.objects.create(
            score_declaration=ScoringDeclaration.objects.create(name="tech_1_score"),
            technology=Technology.objects.create(name="ignore_this_tech"))
        TechImprovement.objects.create(technology=Technology.objects.get(name="ignore_this_tech"))
        TechCollective.objects.create(technology=Technology.objects.get(name='ignore_this_tech'))

        self.assertFalse(self.view.has_not_interested_collectives())

        # Ensure that even if an interest object is created, it does not take it into account if the tech is not advised
        TechCollectiveInterest.objects.create(
            inquirer=self.inquirer,
            tech_collective=TechCollective.objects.get(technology__name='ignore_this_tech'),
            is_interested=False)

    def test_context_data(self):
        context_data = self.view.get_context_data()
        self.assertIn('advised_techs', context_data)
        self.assertIn('has_not_interested_collectives', context_data)