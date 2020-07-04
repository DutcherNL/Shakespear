from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from Questionaire.models import Inquiry, Inquirer
from PageDisplay.models import Page, TextModule
from questionaire_mailing.renderers import MailHTMLRenderer

from questionaire_mailing.mailing import construct_and_send_mail


class MailPage(Page):
    title = models.CharField(max_length=100)
    renderer = MailHTMLRenderer


class MailTask(models.Model):
    name = models.CharField(max_length=56)
    description = models.CharField(max_length=512)
    active = models.BooleanField(default=False, verbose_name="Tigger is active")
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

    def activate(self):
        """ Activates the task and assures that already applicable inquiries don't suddenly get spammed."""
        if not self.active:
            self.active = True
            self.save()
            # Switch states by pretending to send mail, without sending mail
            self.generate_mail(send_mail=False)

    def deactivate(self):
        if self.active:
            self.active = False
            self.save()


class ProcessedMail(models.Model):
    """ A tracker to track which mails have been send and which ones have not."""
    mail = models.ForeignKey(to=MailTask, on_delete=models.CASCADE)
    inquiry = models.ForeignKey(to=Inquiry, on_delete=models.CASCADE, blank=True, null=True)
    inquirer = models.ForeignKey(to=Inquirer, on_delete=models.CASCADE, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    was_applicable = models.BooleanField(verbose_name="Whether the mail has been send")

    class Meta:
        unique_together = ['mail', 'inquiry']

    def clean(self):
        if not (self.inquirer or self.inquiry):
            raise ValidationError("Either inquirer or inquiry needs to have a value")


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

    @property
    def display_general_info(self):
        return f'{self.days_after} dagen na {self.get_trigger_display()}'

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
        """
        Generates mail for all applicable inquiries that apply for this task
        :param send_mail: Whether actual mails should be send.
        If False, mails won't be created, but ProcessedMail instances will be created. defaults True.
        :return: The number of instances processed
        """
        # Get all inquiries that need to be mailed
        inquiries = self.get_all_sendable_inquiries()

        processed = 0

        page_obj = self.layout.get_as_child()

        for inquiry in inquiries:
            mail_send = send_mail

            if send_mail:
                # For each inquiry, construct the mail
                # Send the mail
                email = inquiry.inquirer.email
                if email:
                    construct_and_send_mail(page_obj, {}, email)
                else:
                    mail_send = False

            # For each inquiry send the mail, and process it as send (or not)
            ProcessedMail.objects.create(mail=self, inquiry=inquiry, was_applicable=mail_send)
            processed += 1
        return processed


class TriggeredMailTask(MailTask):
    TRIGGER_MAIL_REGISTERED = "MR"
    TRIGGER_MAIL_CHANGED = "MRN"
    TRIGGER_INQUIRY_COMPLETE = "IC"
    EVENT_CHOICES = [
        (TRIGGER_MAIL_REGISTERED, 'After mail registration in requiry'),
        (TRIGGER_MAIL_CHANGED, 'After mail change in user-settings'),
        (TRIGGER_INQUIRY_COMPLETE, 'After inquiry completion'),
    ]
    event = models.CharField(max_length=3, choices=EVENT_CHOICES)

    @property
    def type(self):
        return "Triggered mail"

    @classmethod
    def trigger(cls, event_type, inquiry=None, inquirer=None, email=None):
        if not (inquirer or inquiry):
            raise AssertionError("Either an inquiry or inquirer should be given")

        active_mail_task = cls.objects.filter(event=event_type, active=True).first()
        if active_mail_task is not None:
            active_mail_task.generate_mail(inquiry=inquiry, inquirer=inquirer, send_mail=True, email=email)

    @property
    def display_general_info(self):
        return f'{self.get_event_display()}'

    def activate(self):
        # Disable any other active mail triggers of the same type.
        if not self.active:
            TriggeredMailTask.objects.filter(event=self.event, active=True).update(active=False)
        # Call the super
        return super(TriggeredMailTask, self).activate()

    def generate_mail(self, inquiry=None, inquirer=None, send_mail=False, email=None):
        """
        Creates the email from the given inquiry
        :param inquiry:
        :param inquirer:
        :param send_mail:
        :return:
        """
        if not send_mail:
            # Mail should not be send, for triggers we do not track if triggers should have been triggered in the past
            # Because it can not activate again by any other means than the actual event trigger.
            return

        # Get the email
        if email is None:
            if inquirer:
                email = inquirer.email
            elif inquiry:
                email = inquiry.inquirer.email

        if email:
            context = {
                'inquiry': inquiry,
                'inquirer': inquirer,
            }

            construct_and_send_mail(self.layout.get_as_child(), context, email)
            ProcessedMail.objects.create(mail=self, inquiry=inquiry, inquirer=inquirer, was_applicable=True)


# Import the modules
from questionaire_mailing.modules.modules import *
