import datetime
from django.test import TestCase, RequestFactory
from django.utils import timezone

from initiative_enabler.views import *
from initiative_enabler.tests import set_up_rsvp


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
        self.setUp_view()

    def setUp_view(self, url_code=None):
        self.view = CollectiveRSVPView()
        url_code = url_code or self.rsvp.url_code
        self.view.setup(self.get_request, rsvp_slug=url_code)

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

    def test_rsvp_view_already_activated(self):
        self.rsvp.activated = True
        self.rsvp.save()
        self.setUp_view()

        response = self.view.dispatch(self.get_request, url_code='no_match')
        self.assertEqual(response.template_name[0], "initiative_enabler/rsvps/rsvp_collective_already_activated.html")
        self.assertEqual(response.status_code, 410)  # HTTP Gone


