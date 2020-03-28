from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone

from Questionaire.models import Inquiry
from PageDisplay.models import Page, TextModule
from questionaire_mailing.renderers import MailRenderer

from questionaire_mailing.mailing import construct_and_send_mail


class MailPage(Page):
    title = models.CharField(max_length=100)
    renderer = MailRenderer


class MailTask(models.Model):
    name = models.CharField(max_length=56)
    description = models.CharField(max_length=512)
    active = models.BooleanField(default=False, verbose_name="Whether these mails are being send")
    layout = models.ForeignKey(Page, on_delete=models.CASCADE, blank=True, editable=False)

    def save(self, *args, **kwargs):
        if not hasattr(self, 'layout'):
            self.layout = MailPage.objects.create(name=self.name, title=self.name)
            self.layout.add_basic_module(TextModule, text="Hallo,")
            self.layout.add_basic_module(TextModule, text="Met vriendelijke groet,\n\nDe klimaat menukaart")

        return super(MailTask, self).save(*args, **kwargs)

    @property
    def type(self):
        sublcass = self.get_as_child()
        return sublcass.type

    def get_as_child(self):
        """ Returns the child object of this class"""
        # Loop over all children
        for child in self.__class__.__subclasses__():
            # If the child object exists
            if child.objects.filter(id=self.id).exists():
                return child.objects.get(id=self.id).get_as_child()
        return self


class ProcessedMail(models.Model):
    """ A tracker to track which mails have been send and which ones have not."""
    mail = models.ForeignKey(to=MailTask, on_delete=models.CASCADE)
    inquiry = models.ForeignKey(to=Inquiry, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    was_applicable = models.BooleanField(verbose_name="Whether the mail has been send")

    class Meta:
        unique_together = ['mail', 'inquiry']


class TimedMailTask(MailTask):
    days_after = models.IntegerField(default=7)

    AFTER_COMPLETION = 'TC'
    AFTER_CREATION_INCOMPLETE = 'TI'
    AFTER_LAST_LOGIN_COMPLETED = 'LC'
    AFTER_LAST_LOGIN_INCOMPLETE = 'LI'
    TRIGGER_CHOICES = [
        (AFTER_COMPLETION, 'After completion'),
        (AFTER_CREATION_INCOMPLETE, 'After creation (incomplete)'),
        (AFTER_LAST_LOGIN_COMPLETED, 'After Last Login (Completed)'),
        (AFTER_LAST_LOGIN_INCOMPLETE, 'After Last Login (Incomplete)'),
    ]
    trigger = models.CharField(max_length=2, choices=TRIGGER_CHOICES)

    @property
    def type(self):
        return "Timed mail"

    def get_all_sendable_inquiries(self, datetime=None):
        if datetime is None:
            datetime = timezone.now()

        # Adjust the time to be at the edge
        datetime = datetime - timedelta(days=self.days_after)

        queryset = Inquiry.objects.all()

        # Exclude existing and processed entries
        queryset = queryset.exclude(processedmail__in=ProcessedMail.objects.filter(mail=self))

        if   self.trigger == TimedMailTask.AFTER_COMPLETION:
            queryset = queryset.filter(completed_on__lte=datetime)
        elif self.trigger == TimedMailTask.AFTER_CREATION_INCOMPLETE:
            queryset = queryset.filter(created_on__lte=datetime, is_complete=False)
        elif self.trigger == TimedMailTask.AFTER_LAST_LOGIN_COMPLETED:
            queryset = queryset.filter(last_visited__lte=datetime, is_complete=True)
        elif self.trigger == TimedMailTask.AFTER_LAST_LOGIN_INCOMPLETE:
            queryset = queryset.filter(last_visited__lte=datetime, is_complete=False)

        return queryset

    def generate_mail(self, send_mail=True):
        # Get all inquiries that need to be mailed
        inquiries = self.get_all_sendable_inquiries()

        for inquiry in inquiries:
            mail_send = send_mail

            if send_mail:
                # For each inquiry, construct the mail
                # Send the mail
                email = "test@test.nl"
                if email:
                    construct_and_send_mail(self.layout, {}, email)
                else:
                    mail_send = False

            # For each inquiry send the mail, and process it as send (or not)
            ProcessedMail.objects.create(mail=self, inquiry=inquiry, was_applicable=mail_send)



