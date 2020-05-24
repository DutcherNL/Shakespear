import datetime

from django.forms import Form, ModelForm, ValidationError
from django.core.validators import RegexValidator
from django import forms
from django.contrib import messages
from django.utils import timezone
from django.forms.widgets import HiddenInput
from django.urls import reverse

from mailing.mails import send_templated_mail
from initiative_enabler.models import *
from Questionaire.models import Inquirer


__all__ = ['StartCollectiveFormSimple', 'RSVPAgreeForm', 'RSVPDenyForm', 'RSVPOnClosedForm', 'RSVPRefreshExpirationForm',
           'QuickSendInvitationForm', 'SendReminderForm', 'SwitchCollectiveStateForm', 'EditPersonalDataForm',
           'StartCollectiveFormTwoStep', 'AdjustTechCollectiveForm']


class NoFormDataMixin:
    """ A mixin for forms that contain no field data and thus only need to check for limited direct input
    It allows for retrieval of data suitable with the django messages framework """
    success_message = None

    def get_as_error_message(self):
        """ Returns the validation error as set-up for a message in the django messages framework. The message
        returned is an arbitrary one. However, as validation is done in the same order every time, the resulting
        error herre is deterministic (i.e. returns the same error in similar cricumstances) """
        keys = list(self.errors.keys())
        if len(keys) > 0:
            item = self.errors[keys[0]]
            # Make sure that for some reason an empty error was inserted
            if len(item) > 0:
                error = item[0]
            else:
                # For some reason the error did not have a description
                error = "Een onbekende error heeft plaats gevonden bij verwerken"
        return messages.ERROR, error

    def get_as_succes_message(self):
        return messages.SUCCESS, self.success_message


class CollectiveMixin:
    """ A mixin for adjustments to collective or collective related objects. """

    def __init__(self, *args, collective=None, **kwargs):
        if collective is None:
            raise KeyError("A collective should be given")
        self.collective = collective
        super(CollectiveMixin, self).__init__(*args, **kwargs)


class StartCollectiveFormTwoStep(ModelForm):
    prefix = 'final'

    class Meta:
        model = InitiatedCollective
        fields = ["name", "address", "phone_number", "message"]

    def __init__(self, inquirer, tech_collective, **kwargs):
        self.inquirer = inquirer
        self.tech_collective = tech_collective
        super(StartCollectiveFormTwoStep, self).__init__(**kwargs)

    def get_personal_data_subform(self):
        class CreatePartOneForm(ModelForm):
            prefix = "shell"
            class Meta:
                model = InitiatedCollective
                fields = ["name", "address", "phone_number"]

        return CreatePartOneForm(self.data if bool(self.data) else None)

    def get_message_form(self):
        class CreatePartTwoForm(ModelForm):
            prefix = "final"

            class Meta:
                model = InitiatedCollective
                fields = ["name", "address", "phone_number", 'message']
                widgets = {
                    'name': HiddenInput,
                    'address': HiddenInput,
                    'phone_number': HiddenInput,
                }

        return CreatePartTwoForm(self.data if bool(self.data) else None)

    def save(self, commit=True):
        self.instance.inquirer = self.inquirer
        self.instance.tech_collective = self.tech_collective
        self.instance = super(StartCollectiveFormTwoStep, self).save(commit=commit)

        # Create the invitations and send them as emails
        subject = f'Uitnodiging collectieve inkoop {self.tech_collective.technology}'
        template_name = "collectives/invite_mail"
        context_data = {
            'collective': self.instance
        }

        for uninvited in self.instance.get_uninvited_inquirers():
            new_rsvp = CollectiveRSVP.objects.create(inquirer=uninvited.inquirer, collective=self.instance)

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
        return self.instance


class StartCollectiveFormSimple(ModelForm):
    uitnodiging = forms.CharField()

    class Meta:
        model = InitiatedCollective
        fields = ["name", "address", "phone_number", "uitnodiging"]

    def __init__(self, inquirer, tech_collective, **kwargs):
        self.inquirer = inquirer
        self.tech_collective = tech_collective
        super(StartCollectiveFormSimple, self).__init__(**kwargs)

    def save(self, commit=True):
        self.instance.inquirer = self.inquirer
        self.instance.tech_collective = self.tech_collective
        self.instance = super(StartCollectiveFormSimple, self).save(commit=commit)

        rsvp_targets = self.tech_collective.get_interested_inquirers(self.inquirer)

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
        if self.collective.get_uninvited_inquirers().count() == 0:
            raise ValidationError("Er zijn geen nieuwe personen in uw omgeving om uit te nodigen")

        return self.cleaned_data

    def save(self):
        subject = f'Uitnodiging collectieve inkoop {self.collective.tech_collective.technology}'
        template_name = "collectives/invite_mail"
        context_data = {
            'collective': self.collective
        }

        for uninvited in self.collective.get_uninvited_inquirers():
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
        data_obj.save()


class AdjustTechCollectiveForm(NoFormDataMixin, ModelForm):
    success_on_message = "U ontvangt nu berichten als iemand in uw omgeving een collectief start"
    success_off_message = "U word niet meer geinformeerd over collectieven in uw omgeving"

    class Meta:
        model = TechCollectiveInterest
        fields = ['is_interested']

    def __init__(self, *args, instance=None, inquirer=None, tech_collective=None, **kwargs):
        if instance is None:
            assert inquirer is not None
            assert tech_collective is not None
            try:
                instance = self._meta.model.objects.get(inquirer=inquirer, tech_collective=tech_collective)
            except self._meta.model.DoesNotExist:
                instance = self._meta.model(inquirer=inquirer, tech_collective=tech_collective)

        super(AdjustTechCollectiveForm, self).__init__(*args, instance=instance, **kwargs)

    def get_as_succes_message(self):
        if self.instance.is_interested:
            message = self.success_on_message
        else:
            message = self.success_off_message

        return messages.SUCCESS, message

    def save(self, commit=True):
        super(AdjustTechCollectiveForm, self).save()
        return self.get_as_succes_message()

    def clean_is_interested(self):
        if self.instance.is_interested == self.cleaned_data['is_interested']:
            if self.instance.is_interested:
                raise ValidationError('Wij konden u niet eerder op geïnteresseerd zetten, want dat bent u al.')
            else:
                raise ValidationError('U staat al als niet geïnteresseerd')
        return self.cleaned_data['is_interested']

    def get_post_url(self):
        return reverse('collectives:adjust_tech_interest', kwargs={'collective_id': self.instance.tech_collective.id})
