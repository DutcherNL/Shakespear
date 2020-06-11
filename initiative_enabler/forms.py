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
from Questionaire.models import Inquirer, Technology, InquiryQuestionAnswer
from Questionaire.fields import QuestionFieldFactory


__all__ = ['RSVPAgreeForm', 'RSVPDenyForm', 'RSVPOnClosedForm', 'RSVPRefreshExpirationForm',
           'QuickSendInvitationForm', 'SendReminderForm', 'SwitchCollectiveStateForm', 'EditPersonalDataForm',
           'StartCollectiveFormTwoStep', 'AdjustTechCollectiveInterestForm', 'EnableAllTechCollectiveInterestForm']

# ###########################################
# ################ Mixins ###################
# ###########################################


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

    def get_as_success_message(self):
        return messages.SUCCESS, self.success_message

    def save(self, commit=True):
        if hasattr(super(NoFormDataMixin, self), 'save'):
            super(NoFormDataMixin, self).save()
        return self.get_as_success_message()


class CollectiveMixin:
    """ A mixin for adjustments to collective or collective related objects. """

    def __init__(self, *args, collective=None, **kwargs):
        if collective is None:
            raise KeyError("A collective should be given")
        self.collective = collective
        super(CollectiveMixin, self).__init__(*args, **kwargs)


# ###########################################
# ########### Collective Forms ##############
# ###########################################


class StartCollectiveFormTwoStep(ModelForm):
    prefix = 'final'

    class Meta:
        model = InitiatedCollective
        fields = ["name", "address", "phone_number", "message"]

    def __init__(self, inquirer, tech_collective, **kwargs):
        self.inquirer = inquirer
        self.tech_collective = tech_collective
        super(StartCollectiveFormTwoStep, self).__init__(**kwargs)

    def clean(self):
        for restriction in self.tech_collective.restrictions.all():
            restriction = restriction.get_as_child()
            restriction.has_working_restriction(self.inquirer)

        return self.cleaned_data

    def get_personal_data_subform(self):
        """ Contains a small subset of the larger form, acts as an initial screen with limited information
        copied to final form through javascript on the page """
        class CreatePartOneForm(ModelForm):
            prefix = "shell"
            class Meta:
                model = InitiatedCollective
                fields = ["name", "address", "phone_number"]

        return CreatePartOneForm(self.data if bool(self.data) else None)

    def get_message_form(self):
        """ Contains a small subset of the larger form + the remainders form values in hidden fields """
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
        self.instance.set_restriction_values()

        # Create the invitations and send them as emails
        subject = f'Uitnodiging collectieve inkoop {self.tech_collective.technology}'
        template_name = "collectives/invite_mail"
        context_data = {
            'collective': self.instance
        }

        for uninvited in self.instance.get_uninvited_inquirers():
            new_rsvp = CollectiveRSVP.objects.create(inquirer=uninvited, collective=self.instance)

            context_data.update({
                'rsvp': new_rsvp,
            })
            if uninvited.email:
                send_templated_mail(
                    subject=subject,
                    template_name=template_name,
                    context_data=context_data,
                    recipient=new_rsvp.inquirer
                )
        return self.instance


class QuickSendInvitationForm(CollectiveMixin, NoFormDataMixin, Form):
    """ Sends an invitation to new members with the invitation text defined earlier """
    success_message = "Uitnodigingen zijn verstuurd."

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
            new_rsvp = CollectiveRSVP.objects.create(inquirer=uninvited, collective=self.collective)

            context_data.update({
                'rsvp': new_rsvp,
            })
            if uninvited.email:
                send_templated_mail(
                    subject=subject,
                    template_name=template_name,
                    context_data=context_data,
                    recipient=new_rsvp.inquirer
                )
        return super(QuickSendInvitationForm, self).save()


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

        return super(SendReminderForm, self).save()


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
        return super(SwitchCollectiveStateForm, self).save()

# ###########################################
# ############## RSVP Forms #################
# ###########################################


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
        return super(RSVPDenyForm, self).save()


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
        return super(RSVPOnClosedForm, self).save()


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

        return self.get_as_success_message()


# ###########################################
# ############# Other Forms #################
# ###########################################


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


class AdjustTechCollectiveInterestForm(NoFormDataMixin, ModelForm):
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

        super(AdjustTechCollectiveInterestForm, self).__init__(*args, instance=instance, **kwargs)

    def get_as_success_message(self):
        if self.instance.is_interested:
            message = self.success_on_message
        else:
            message = self.success_off_message

        return messages.SUCCESS, message

    def clean_is_interested(self):
        if self.instance.is_interested == self.cleaned_data['is_interested']:
            if self.instance.is_interested:
                raise ValidationError(
                    'Wij konden u niet eerder op geïnteresseerd zetten, want dat bent u al.',
                    code='already_interested')
            else:
                raise ValidationError(
                    'U staat al als niet geïnteresseerd',
                    code='already_not_interested')
        return self.cleaned_data['is_interested']

    def save(self, commit=True):
        message = super(AdjustTechCollectiveInterestForm, self).save(commit=commit)
        # Update the restriction values (this could also add a new value when disabling notifications if another
        # answer was given in the mean time. Though this should already be added on questionaire completion
        self.instance.set_restriction_values()
        return message

    def get_post_url(self):
        return reverse('collectives:adjust_tech_interest', kwargs={'collective_id': self.instance.tech_collective.id})


class EnableAllTechCollectiveInterestForm(NoFormDataMixin, Form):
    """
    A form that enables interest on all tech collectives
    """
    success_message = "We hebben u genoteerd als geïnteresseerd in alle aanbevolen collectieve acties"

    def __init__(self, *args, collectives=None, inquirer=None, **kwargs):
        assert inquirer is not None
        self.inquirer = inquirer

        if collectives is None:
            self.collectives = TechCollective.objects.all()
        else:
            self.collectives = collectives

        super(EnableAllTechCollectiveInterestForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        for collective in self.collectives:
            try:
                interest = TechCollectiveInterest.objects.get(
                    inquirer=self.inquirer,
                    tech_collective=collective,
                )
                interest.is_interested = True
                interest.save()
            except TechCollectiveInterest.DoesNotExist:
                TechCollectiveInterest.objects.create(
                    inquirer=self.inquirer,
                    tech_collective=collective,
                    is_interested=True,
                )
        return super(EnableAllTechCollectiveInterestForm, self).save()

    @staticmethod
    def get_advised_collectives(inquiry):
        advised_collectives = []
        for collective in TechCollective.objects.all():
            technology = collective.technology
            if technology.get_as_techgroup:
                technology = technology.get_as_techgroup
            tech_score = technology.get_score(inquiry=inquiry)
            if tech_score == Technology.TECH_SUCCESS or tech_score == Technology.TECH_VARIES:
                advised_collectives.append(collective)
        return advised_collectives


class RestrictionFormMixin:
    field_name = None

    def __init__(self, *args, restriction: CollectiveQuestionRestriction = None, inquirer: Inquirer = None, **kwargs):
        assert restriction is not None
        assert inquirer is not None
        self.restriction = restriction
        self.inquirer = inquirer
        super(RestrictionFormMixin, self).__init__(*args, **kwargs)

        field = self.generate_field()
        self.field_name = self.field_name or field.name
        self.fields[self.field_name] = field

    def generate_field(self):
        """ Returns a field to answer the value in """
        raise NotImplementedError


class UpdateQuestionRestrictionForm(RestrictionFormMixin, Form):
    """ An abstraction of the various forms """

    def generate_field(self):
        field = QuestionFieldFactory.get_field_by_questionmodel(
            self.restriction.question,
            inquiry=self.inquirer.active_inquiry,
            required=True)
        return field

    def save(self):
        self.restriction.question.answer_for_inquiry(
            self.inquirer.active_inquiry,
            self.cleaned_data[self.field_name],
            False)
