from datetime import datetime
from django.core import mail
from django.test import TestCase

from questionaire_mailing.models import TimedMailTask, ProcessedMail


class TimedMailTaskTest(TestCase):
    fixtures = ['questionaire_mailing/tests/fixtures/test_fixtures.json']

    def assertExists(self, model, **kwargs):
        try:
            return self.assertTrue(model.objects.filter(**kwargs).exists())
        except AssertionError as e:
            raise e

    def setUp(self):
        # Set up the database
        self.timed_task_1 = TimedMailTask.objects.create(name="task_after_7", days_after=7, trigger=TimedMailTask.AFTER_COMPLETION)
        self.timed_task_2 = TimedMailTask.objects.create(name="task_after_7", days_after=7, trigger=TimedMailTask.AFTER_CREATION_INCOMPLETE)
        self.timed_task_3 = TimedMailTask.objects.create(name="task_after_7", days_after=7, trigger=TimedMailTask.AFTER_LAST_LOGIN_COMPLETED)
        self.timed_task_4 = TimedMailTask.objects.create(name="task_after_7", days_after=7, trigger=TimedMailTask.AFTER_LAST_LOGIN_INCOMPLETE)

    def test_timed_mail_task_query(self):
        """ Tests whether the emails are send according to the script at the right time.
        I.e. tests the day_after the trigger occurs """
        dt_string = "15/01/2020 00:00:00"
        dt_test = datetime.strptime(dt_string, "%d/%m/%Y %H:%M:%S")

        self.assertEqual(self.timed_task_1.get_all_sendable_inquiries(datetime=dt_test).count(), 2)
        self.assertEqual(self.timed_task_2.get_all_sendable_inquiries(datetime=dt_test).count(), 3)
        self.assertEqual(self.timed_task_3.get_all_sendable_inquiries(datetime=dt_test).count(), 1)
        self.assertEqual(self.timed_task_4.get_all_sendable_inquiries(datetime=dt_test).count(), 2)

    def test_processed_exclusion(self):
        """ Tests whether already processed mails are not selected when assesing all mails that need to be send. """
        dt_string = "15/01/2020 00:00:00"
        dt_test = datetime.strptime(dt_string, "%d/%m/%Y %H:%M:%S")

        # Test the base state for the mailing tasks
        self.assertEqual(self.timed_task_1.get_all_sendable_inquiries(datetime=dt_test).count(), 2)
        self.assertEqual(self.timed_task_3.get_all_sendable_inquiries(datetime=dt_test).count(), 1)

        # Test that send mails are not send again.
        ProcessedMail.objects.create(mail=self.timed_task_1, inquiry_id=1, was_applicable=False)
        ProcessedMail.objects.create(mail=self.timed_task_1, inquiry_id=5, was_applicable=False)
        self.assertEqual(self.timed_task_1.get_all_sendable_inquiries(datetime=dt_test).count(), 1)
        self.assertEqual(self.timed_task_3.get_all_sendable_inquiries(datetime=dt_test).count(), 1)

        # Create additional send mails to see if it changes the state correctly.
        ProcessedMail.objects.create(mail=self.timed_task_3, inquiry_id=1, was_applicable=False)
        ProcessedMail.objects.create(mail=self.timed_task_3, inquiry_id=6, was_applicable=True)
        self.assertEqual(self.timed_task_1.get_all_sendable_inquiries(datetime=dt_test).count(), 1)
        self.assertEqual(self.timed_task_3.get_all_sendable_inquiries(datetime=dt_test).count(), 0)

    def test_processed_mail_creation(self):
        """ Test that mail generation automatically creates a processed_mail instance"""
        self.timed_task_1.generate_mail(send_mail=False)
        # Check that one of the processed mail objects is created
        self.assertExists(ProcessedMail, mail=self.timed_task_1, inquiry_id=6)
        # Check that no instances are created that did not apply
        self.assertEqual(ProcessedMail.objects.filter(mail=self.timed_task_1).count(), 2)

    def test_mailing(self):
        self.timed_task_1.generate_mail(send_mail=True)

        # Test that one mail has actually been sent.
        self.assertEqual(len(mail.outbox), 2)
        mail_obj = mail.outbox[0]
        self.assertEqual(mail_obj.subject, self.timed_task_1.layout.title)
        self.assertEqual(mail_obj.alternatives[0][1], 'text/html')





