import datetime

from django.db import models

from Questionaire.models import Inquiry
from PageDisplay.models import Page, TextModule
from questionaire_mailing.renderers import MailRenderer


class MailPage(Page):
    renderer = MailRenderer


class MailTask(models.Model):
    name = models.CharField(max_length=56)
    description = models.CharField(max_length=512)
    active = models.BooleanField(default=False, verbose_name="Whether these mails are being send")
    layout = models.ForeignKey(Page, on_delete=models.CASCADE, blank=True, editable=False)

    def save(self, *args, **kwargs):
        if not hasattr(self, 'layout'):
            self.layout = MailPage.objects.create(name=self.name)
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

    AFTER_COMPLETEION = 'TC'
    AFTER_CREATION_INCOMPLETE = 'TI'
    AFTER_LAST_LOGIN_COMPLETED = 'LC'
    AFTER_LAST_LOGIN_INCOMPLETE = 'LI'
    TRIGGER_CHOICES = [
        (AFTER_COMPLETEION, 'After completion'),
        (AFTER_CREATION_INCOMPLETE, 'After creation (incomplete)'),
        (AFTER_LAST_LOGIN_COMPLETED, 'After Last Login (Completed)'),
        (AFTER_LAST_LOGIN_INCOMPLETE, 'After Last Login (Incomplete)'),
    ]
    trigger = models.CharField(max_length=2, choices=TRIGGER_CHOICES)

    @property
    def type(self):
        return "Timed mail"

