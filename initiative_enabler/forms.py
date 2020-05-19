import datetime

from django.forms import Form, ModelForm, ValidationError
from django.core.validators import RegexValidator
from django import forms
from django.contrib import messages
from django.utils import timezone

from mailing.mails import send_templated_mail
from initiative_enabler.models import *
from Questionaire.models import Inquirer


__all__ = ['StartCollectiveForm', 'RSVPAgreeForm', 'RSVPDenyForm', 'RSVPOnClosedForm', 'RSVPRefreshExpirationForm',
           'QuickSendInvitationForm', 'SendReminderForm', 'SwitchCollectiveStateForm', 'EditPersonalDataForm']


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

    def __init__(self, *args, collective=None, **kwargs):
        if collective is None:
            raise KeyError("A collective should be given")
        self.collective = collective
        super(CollectiveMixin, self).__init__(*args, **kwargs)


class StartCollectiveForm(ModelForm):
    uitnodiging = forms.CharField()

    class Meta:
        model = InitiatedCollective
        fields = ["name", "address", "phone_number", "uitnodiging"]

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

        return super(RSVPAgreeForm, self).clean()

    def save(self, commit=True):
        self.instance.collective = self.rsvp.collective
        self.instance.inquirer = self.rsvp.inquirer
        self.instance = super(RSVPAgreeForm, self).save(commit=commit)

        self.rsvp.activated = True
        self.rsvp.save()
        return self.instance


class RSVPDenyForm(NoFormDataMixin, Form):
    success_message = "je hebt de uitnodiging afgewezen"

    def __init__(self, rsvp, **kwargs):
        self.rsvp = rsvp
        super(RSVPDenyForm, self).__init__(**kwargs)

    def clean(self):
        if self.rsvp.activated:
            raise ValidationError("Deze uitnodiging is al reeds behandeld")

        return super(RSVPDenyForm, self).clean()

    def save(self, commit=True):
        CollectiveDeniedResponse.objects.create(collective=self.rsvp.collective, inquirer=self.rsvp.inquirer)
        self.rsvp.activated = True
        self.rsvp.save()
        return self.get_as_succes_message()


class RSVPOnClosedForm(NoFormDataMixin, Form):
    success_message = "Je staat nu geregistreerd als geïnteresseerd. Wanneer de collectief weer word geopend krijg" \
                      "je automatisch bericht."

    def __init__(self, rsvp, *args, **kwargs):
        self.rsvp = rsvp
        super(RSVPOnClosedForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.rsvp.collective.is_open:
            raise ValidationError("Collectief is nog steeds open.")

        if self.rsvp.activated:
            raise ValidationError("Deze uitnodiging is al reeds behandeld")

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

    def clean(self):
        if self.rsvp.activated:
            raise ValidationError("Dit verzoek is al reeds behandeld")
        
        return super(RSVPRefreshExpirationForm, self).clean()

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


class QuickSendInvitationForm(CollectiveMixin, NoFormDataMixin, Form):
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
    days_between = 5

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
            if open_rsvp.last_send_on + datetime.timedelta(days=self.days_between) <= timezone.now():
                # Ensure no mails are send if it has been to recent
                if open_rsvp.inquirer.email:
                    send_templated_mail(
                        subject=subject,
                        template_name=template_name,
                        context_data=context_data,
                        recipient=open_rsvp.inquirer
                    )

                # Refresh the invitation
                open_rsvp.last_send_on = timezone.now()
                open_rsvp.save()

        return self.get_as_succes_message()


class SwitchCollectiveStateForm(CollectiveMixin, NoFormDataMixin, Form):
    to_state = forms.BooleanField(required=False)

    def clean(self):
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


class EditPersonalDataForm(Form):
    name = forms.CharField()
    adres = forms.CharField()
    tel_nummer = forms.CharField(validators=[
        RegexValidator("^((\+[1-9]{2})|(00[1-9]{2})|(0[1-9]{1,2}))[ -]{0,1}[1-9]*$",
                       message="Vul in geldig telefoonnummer in", code='invalid_phone_number')])

    def __init__(self, *args, inquirer=None, collective=None, **kwargs):
        assert inquirer is not None, "Inquirer is niet gegeven"
        assert collective is not None, "Collectief is niet gegeven"
        self.inquirer = inquirer
        self.collective = collective

        kwargs.setdefault('initial', {})
        kwargs['initial'].update(self.set_initial_values())
        super(EditPersonalDataForm, self).__init__(*args, **kwargs)

    def set_initial_values(self):
        if self.inquirer == self.collective.inquirer:
            data_object = self.collective
        else:
            try:
                as_approved_inquirer = self.collective.collectiveapprovalresponse_set.get(inquirer=self.inquirer)
                data_object = as_approved_inquirer
            except CollectiveApprovalResponse.DoesNotExist:
                pass

        initials = {
            'name': data_object.name,
            'adres': data_object.address,
            'tel_nummer': data_object.phone_number
        }

        return initials

    def clean(self):
        cleaned_data = self.cleaned_data
        if self.inquirer == self.collective.inquirer:
            cleaned_data['inquirer_data_container'] = self.collective
        else:
            try:
                as_approved_inquirer = self.collective.collectiveapprovalresponse_set.get(inquirer=self.inquirer)
                cleaned_data['inquirer_data_container'] = as_approved_inquirer
            except CollectiveApprovalResponse.DoesNotExist:
                raise ValidationError("Jij bent niet betrokken bij dit collectief dus ook geen persoonlijke data")

    def save(self):
        data_obj = self.cleaned_data['inquirer_data_container']
        data_obj.name = self.cleaned_data['name']
        data_obj.address = self.cleaned_data['adres']
        data_obj.phone_number = self.cleaned_data['tel_nummer']
        print(data_obj)
        data_obj.save()
