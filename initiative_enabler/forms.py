from django.forms import Form, CharField, ModelForm, ValidationError
from django import forms
from django.contrib import messages

from mailing.mails import send_templated_mail
from initiative_enabler.models import *


class NoFormDataMixin:
    """ A mixin for forms that contain no field data and thus only need to check for limited direct input
    It allows for retrieval of data suitable with the django messages framework """
    success_message = None

    def get_as_error_message(self):
        """ Returns the validation error as set-up for a message in the django messages framework"""
        return messages.ERROR, self.non_field_errors()[0]

    def get_as_succes_message(self):
        return messages.SUCCESS, self.success_message


class CollectiveMixin:
    """ A mixin for adjustments to collective or collective related objects. """

    def __init__(self, *args, collective=None, current_inquirer=None, **kwargs):
        if collective is None:
            raise KeyError("A collective should be given")
        self.collective = collective
        self.current_inquirer = current_inquirer
        super(CollectiveMixin, self).__init__(*args, **kwargs)


class StartCollectiveForm(ModelForm):
    uitnodiging = CharField()

    class Meta:
        model = InitiatedCollective
        fields = ["name", "host_address", "phone_number", "uitnodiging"]

    def __init__(self, inquirer, tech_collective, **kwargs):
        self.inquirer = inquirer
        self.tech_collective = tech_collective
        super(StartCollectiveForm, self).__init__(**kwargs)

    def save(self, commit=True):
        self.instance.inquirer = self.inquirer
        self.instance.tech_collective = self.tech_collective
        self.instance = super(StartCollectiveForm, self).save(commit=commit)

        inquiries = self.tech_collective.get_similar_inquiries(self.inquirer.active_inquiry)
        rsvp_targets = Inquirer.objects.filter(inquiry__in=inquiries).distinct().exclude(id=self.inquirer.id)

        for target in rsvp_targets:
            CollectiveRSVP.objects.create(collective=self.instance,
                                          inquirer=target)
            # TODO: Send mail accoriding to all RSVP objects
        return self.instance


class RSVPAgreeForm(ModelForm):
    class Meta:
        model = CollectiveApprovalResponse
        fields = ["name", "address", "phone_number", "message"]

    def __init__(self, rsvp, **kwargs):
        self.rsvp = rsvp
        super(RSVPAgreeForm, self).__init__(**kwargs)

    def clean(self):
        if self.rsvp.activated:
            raise ValidationError("Dit verzoek is al reeds behandeld")
        if not self.rsvp.collective.is_open:
            raise ValidationError("Dit collectief is inmiddels niet meer toegankelijk.")

    def save(self, commit=True):
        self.instance.collective = self.rsvp.collective
        self.instance.inquirer = self.rsvp.inquirer
        self.instance = super(RSVPAgreeForm, self).save(commit=commit)

        self.rsvp.activated = True
        self.rsvp.save()
        return self.instance


class RSVPDisagreeForm(ModelForm):
    class Meta:
        model = CollectiveDeniedResponse
        fields = []

    def __init__(self, rsvp, **kwargs):
        self.rsvp = rsvp
        super(RSVPDisagreeForm, self).__init__(**kwargs)

    def clean(self):
        if self.rsvp.activated:
            raise ValidationError("Dit verzoek is al reeds behandeld")

    def save(self, commit=True):
        self.instance.collective = self.rsvp.collective
        self.instance.inquirer = self.rsvp.inquirer
        self.instance = super(RSVPDisagreeForm, self).save(commit=commit)

        self.rsvp.activated = True
        self.rsvp.save()
        return self.instance


class RSVPOnClosedForm(NoFormDataMixin, Form):
    success_message = "Processed"

    def __init__(self, rsvp, *args, **kwargs):
        self.rsvp = rsvp
        super(RSVPOnClosedForm, self).__init__(*args, **kwargs)

    def save(self):
        CollectiveRSVPInterest.objects.create(collective=self.rsvp.collective, inquirer=self.rsvp.inquirer)
        self.rsvp.activated = True
        self.rsvp.save()
        return self.get_as_succes_message()


class RSVPRefreshExpirationForm(NoFormDataMixin, Form):
    success_message = "A mail has been send to the email adress registered"

    def __init__(self, rsvp, *args, **kwargs):
        self.rsvp = rsvp
        super(RSVPRefreshExpirationForm, self).__init__(*args, **kwargs)

    def send(self):
        new_rsvp = CollectiveRSVP.objects.create(collective=self.rsvp.collective, inquirer=self.rsvp.inquirer)
        self.rsvp.activated = True
        self.rsvp.save()

        subject = f'Uitnodiging voor collectieve installatie {new_rsvp.collective.tech_collective.technology}'
        template_name = "collectives/invite_mail"
        context_data = {
            'collective': new_rsvp.collective,
            'rsvp': new_rsvp
        }

        if new_rsvp.inquirer.email:
            send_templated_mail(
                subject=subject,
                template_name=template_name,
                context_data=context_data,
                recipient=new_rsvp.inquirer
            )

        return self.get_as_succes_message()


class SendInvitationForm(CollectiveMixin, NoFormDataMixin, Form):
    success_message = "Uitnodigingen zijn verstuurd. RSVPs alleen niet aangemaakt"

    def clean(self):
        if not self.collective.is_open:
            raise ValidationError("Collectief is niet meer open. Nieuwe contacten kunnen niet worden uitgenodigd.")
        if self.collective.get_uninvited_inquiries().count() == 0:
            raise ValidationError("Er zijn geen nieuwe personen in uw omgeving om uit te nodigen")

        return self.cleaned_data

    def save(self):
        subject = f'Herinnering: collectieve inkoop {self.collective.tech_collective.technology}'
        template_name = "collectives/invite_mail"
        context_data = {
            'collective': self.collective
        }

        for uninvited in self.collective.get_uninvited_inquiries():
            new_rsvp = CollectiveRSVP.objects.create(inquirer=uninvited.inquirer, collective=self.collective)

            context_data.update({
                'rsvp': new_rsvp,
            })
            if uninvited.inquirer.email:
                send_templated_mail(
                    subject=subject,
                    template_name=template_name,
                    context_data=context_data,
                    recipient=new_rsvp.inquirer
                )
        return self.get_as_succes_message()


class SendReminderForm(CollectiveMixin, NoFormDataMixin, Form):
    success_message = "Herinneringen zijn verstuurd"

    def clean(self):
        if not self.collective.is_open:
            raise ValidationError("Collectief is niet meer open. Reminders kunnen niet gestuurd worden")
        if CollectiveRSVP.objects.filter(activated=False).count() == 0:
            # Todo, timestamp filter
            raise ValidationError("Alle uitnodigingen zijn al beantwoord")

        return self.cleaned_data

    def save(self):
        subject = f'Herinnering: collectieve inkoop {self.collective.tech_collective.technology}'
        template_name = "collectives/reminder_mail"
        context_data = {
            'collective': self.collective
        }

        for open_rsvp in self.collective.open_rsvps():
            context_data.update({
                'rsvp': open_rsvp,
            })
            if open_rsvp.inquirer.email:
                send_templated_mail(
                    subject=subject,
                    template_name=template_name,
                    context_data=context_data,
                    recipient=open_rsvp.inquirer
                )

        return self.get_as_succes_message()


class SwitchCollectiveStateForm(CollectiveMixin, NoFormDataMixin, Form):
    to_state = forms.BooleanField(required=False)

    def clean(self):
        print(self.cleaned_data)
        if self.cleaned_data.get('to_state', False) and self.collective.is_open:
            raise ValidationError("Collectief is al open")
        if not self.cleaned_data.get('to_state', False) and not self.collective.is_open:
            raise ValidationError("Collectief is al gesloten")

        return self.cleaned_data

    def save(self):
        self.collective.is_open = self.cleaned_data.get('to_state', False)
        self.collective.save()
        if self.collective.is_open:
            self.success_message = "Collectief is weer geopend"
        else:
            self.success_message = "Collectief is vanaf nu gesloten. Anderen kunnen niet meer toetreden"
        return self.get_as_succes_message()
