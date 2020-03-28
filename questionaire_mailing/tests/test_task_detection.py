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
        dt_string = "15/01/2020 00:00:00"
        dt_test = datetime.strptime(dt_string, "%d/%m/%Y %H:%M:%S")

        self.assertEqual(self.timed_task_1.get_all_sendable_inquiries(datetime=dt_test).count(), 2)
        self.assertEqual(self.timed_task_2.get_all_sendable_inquiries(datetime=dt_test).count(), 3)
        self.assertEqual(self.timed_task_3.get_all_sendable_inquiries(datetime=dt_test).count(), 1)
        self.assertEqual(self.timed_task_4.get_all_sendable_inquiries(datetime=dt_test).count(), 2)

    def test_processed_exclusion(self):
        dt_string = "15/01/2020 00:00:00"
        dt_test = datetime.strptime(dt_string, "%d/%m/%Y %H:%M:%S")
        ProcessedMail.objects.create(mail=self.timed_task_1, inquiry_id=1, was_applicable=False)
        ProcessedMail.objects.create(mail=self.timed_task_1, inquiry_id=5, was_applicable=False)

        self.assertEqual(self.timed_task_1.get_all_sendable_inquiries(datetime=dt_test).count(), 1)
        self.assertEqual(self.timed_task_3.get_all_sendable_inquiries(datetime=dt_test).count(), 1)

        ProcessedMail.objects.create(mail=self.timed_task_3, inquiry_id=1, was_applicable=False)
        ProcessedMail.objects.create(mail=self.timed_task_3, inquiry_id=6, was_applicable=True)

        self.assertEqual(self.timed_task_1.get_all_sendable_inquiries(datetime=dt_test).count(), 1)
        self.assertEqual(self.timed_task_3.get_all_sendable_inquiries(datetime=dt_test).count(), 0)

    def test_processed_mail_creation(self):
        self.timed_task_1.generate_mail(send_mail=False)

        self.assertExists(ProcessedMail, mail=self.timed_task_1, inquiry_id=6)
        self.assertEqual(ProcessedMail.objects.filter(mail=self.timed_task_1).count(), 2)

    def test_mailing(self):
        self.timed_task_1.generate_mail(send_mail=True)

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 2)
        mail_obj = mail.outbox[0]
        self.assertEqual(mail_obj.subject, self.timed_task_1.layout.title)
        self.assertEqual(mail_obj.alternatives[0][1], 'text/html')

        print(mail_obj.message())





