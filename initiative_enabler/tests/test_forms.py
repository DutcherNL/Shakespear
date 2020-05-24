import datetime
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from Questionaire.models import *
from initiative_enabler.models import *
from initiative_enabler.forms import *
from initiative_enabler.tests import *


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


class CollectiveFormTestCase(QuickTestAdjustmentsMixin, TestCase):
    def setUp(self):
        # Set up the database
        set_up_rsvp(self)

    def test_invitation_form(self):
        """ Tests QuickSendInvitationForm """
        # Test that reminders can't be send when collective is closed
        self.open_collective(True)
        form = QuickSendInvitationForm(data={}, collective=self.collective)
        # There are no inquiries that can be added
        self.assertFalse(form.is_valid())

        # Create an inquiry that can be quickly invited
        inquiry = Inquiry.objects.create(
            inquirer=Inquirer.objects.create(email="tester@testing.io")
        )
        # Override the inquiry retrieval (this method is tested in test_models, so we can shortcut this
        def get_uninvited_override():
            """ Override the uninvited query method to prevent setting up all declarations (aka be lazy) """
            return Inquiry.objects.filter(id=inquiry.id)
        self.collective.get_uninvited_inquirers = get_uninvited_override

        form = QuickSendInvitationForm(data={}, collective=self.collective)
        self.assertTrue(form.is_valid())

        # Test validation of collective opened state
        self.open_collective(False)
        form = QuickSendInvitationForm(data={}, collective=self.collective)
        self.assertFalse(form.is_valid())
        self.open_collective(True)
        form = QuickSendInvitationForm(data={}, collective=self.collective)

        # Test RSVP creation and mail sending
        rsvp_count = CollectiveRSVP.objects.count()
        self.assertEqual(len(mail.outbox), 0)
        form.save()
        self.assertEqual(CollectiveRSVP.objects.count(), rsvp_count + 1)
        self.assertEqual(CollectiveRSVP.objects.last().inquirer, inquiry.inquirer)
        self.assertEqual(len(mail.outbox), 1)

    def test_reminder_form(self):
        """ Tests SendReminderForm """
        # Test that reminders can't be send when collective is closed
        self.open_collective(False)
        form = SendReminderForm(data={}, collective=self.collective)
        self.assertFalse(form.is_valid())

        self.open_collective(True)
        form = SendReminderForm(data={}, collective=self.collective)
        self.assertTrue(form.is_valid())

        # Test that it does not validate when all invitations have been answered
        # Because of this direct update, activated_on is not adjusted, this should not make a difference
        CollectiveRSVP.objects.update(activated=True)
        form = SendReminderForm(data={}, collective=self.collective)
        self.assertFalse(form.is_valid())

        CollectiveRSVP.objects.filter(id=self.rsvp.id).update(activated=False)
        form = SendReminderForm(data={}, collective=self.collective)
        self.assertTrue(form.is_valid())

        # Test that the object has not send because it is to recent
        last_send_on = self.set_rsvp_last_send(now=True, hours=1)
        form.save()
        self.rsvp.refresh_from_db()
        self.assertEqual(self.rsvp.last_send_on, last_send_on)
        self.assertEqual(len(mail.outbox), 0)

        # Test that it is send when it has been too long
        self.set_rsvp_last_send(now=True, days=10)
        now = timezone.now()
        form.save()
        self.rsvp.refresh_from_db()
        self.assertGreaterEqual(self.rsvp.last_send_on, now)
        self.assertEqual(len(mail.outbox), 1)

        # Test rsvps without email
        new_rsvp = CollectiveRSVP.objects.create(
            inquirer=Inquirer.objects.create(),
            collective=self.collective,
            last_send_on=timezone.now() - datetime.timedelta(days=10),
        )
        form.save()
        new_rsvp.refresh_from_db()
        self.assertGreaterEqual(new_rsvp.last_send_on, now)
        self.assertEqual(len(mail.outbox), 1)

    def test_switch_state_form(self):
        """ Test that switching occurs correctly """
        self.assertTrue(self.collective.is_open)
        data = {'to_state': True}
        form = SwitchCollectiveStateForm(data=data, collective=self.collective)
        self.assertFalse(form.is_valid())

        data = {'to_state': False}
        form = SwitchCollectiveStateForm(data=data, collective=self.collective)
        self.assertTrue(form.is_valid())

        # Test form saving (close collective)
        form.save()
        self.collective.refresh_from_db()
        self.assertFalse(self.collective.is_open)

        data = {'to_state': False}
        form = SwitchCollectiveStateForm(data=data, collective=self.collective)
        self.assertFalse(form.is_valid())
        data = {'to_state': True}
        form = SwitchCollectiveStateForm(data=data, collective=self.collective)
        self.assertTrue(form.is_valid())

        # Test form saving (open collective)
        form.save()
        self.collective.refresh_from_db()
        self.assertTrue(self.collective.is_open)


class RSVPFormsTestCase(QuickTestAdjustmentsMixin, TestCase):
    def setUp(self):
        # Set up the database
        set_up_rsvp(self)

    def test_agree_form(self):
        data = {
            'name': "My name",
            'address': "My location",
            'phone_number': "My phone number",
            'message': "My invitation message"
        }
        self.assertTrue(RSVPAgreeForm(data=data, rsvp=self.rsvp).is_valid())

        # Form does not work on closed collectives
        self.open_collective(False)
        self.assertFalse(RSVPAgreeForm(data=data, rsvp=self.rsvp).is_valid())

        self.open_collective(True)
        form = RSVPAgreeForm(data=data, rsvp=self.rsvp)
        form.save()
        self.rsvp.refresh_from_db()

        # Ensure expected processing works accordingly
        self.assertTrue(self.rsvp.activated)
        self.assertEqual(CollectiveApprovalResponse.objects.count(), 1)
        agree_rsvp = CollectiveApprovalResponse.objects.last()
        self.assertEqual(agree_rsvp.inquirer, self.rsvp.inquirer)
        self.assertEqual(agree_rsvp.collective, self.rsvp.collective)

        # RSVP is now processed, so form should no longer be valid
        self.assertFalse(RSVPAgreeForm(data=data, rsvp=self.rsvp).is_valid())

    def test_deny_rsvp_form(self):
        """ test the RSVPDenyForm
        Note: An invitation can be rejected regardless of the state of the collective
        """
        form = RSVPDenyForm(data={}, rsvp=self.rsvp)
        self.assertTrue(form.is_valid())

        rsvp_count = CollectiveDeniedResponse.objects.count()
        form.save()
        # Ensure the RSVP is set to activated
        self.assertTrue(self.rsvp.activated)
        # Assert that a new denied rsvp object is created on the database
        self.assertEqual(CollectiveDeniedResponse.objects.count(), rsvp_count + 1)
        disagree_rsvp = CollectiveDeniedResponse.objects.last()
        self.assertEqual(disagree_rsvp.inquirer, self.rsvp.inquirer)
        self.assertEqual(disagree_rsvp.collective, self.rsvp.collective)

        # RSVP is now set to activated, ensure it can not be triggered again
        self.rsvp.refresh_from_db()
        form = RSVPDenyForm(data={}, rsvp=self.rsvp)
        self.assertFalse(form.is_valid())

    def test_refresh_form(self):
        """ Test the mail refreshment form """
        self.set_rsvp_last_send(days=14)
        form = RSVPRefreshExpirationForm(data={}, rsvp=self.rsvp)
        self.assertTrue(form.is_valid())
        rsvp_count = CollectiveRSVP.objects.count()
        form.send()
        self.assertTrue(self.rsvp.activated)
        self.assertEqual(CollectiveRSVP.objects.count(), rsvp_count + 1)
        self.assertEqual(len(mail.outbox), 1)

        # RSVP is now set to activated, ensure it can not be triggered again
        self.rsvp.refresh_from_db()
        form = RSVPRefreshExpirationForm(data={}, rsvp=self.rsvp)
        self.assertFalse(form.is_valid())

    def test_interest_after_closure_form(self):
        self.assertFalse(RSVPOnClosedForm(data={}, rsvp=self.rsvp).is_valid())

        self.open_collective(False)
        form = RSVPOnClosedForm(data={}, rsvp=self.rsvp)
        self.assertTrue(form.is_valid())

        form.save()
        self.rsvp.refresh_from_db()

        self.assertTrue(self.rsvp.activated)
        self.assertEqual(CollectiveRSVPInterest.objects.count(), 1)
        interest = CollectiveRSVPInterest.objects.last()
        self.assertEqual(interest.collective, self.rsvp.collective)
        self.assertEqual(interest.inquirer, self.rsvp.inquirer)

        # Form is not valid when RSVP is already activated
        self.assertFalse(RSVPOnClosedForm(data={}, rsvp=self.rsvp).is_valid())
