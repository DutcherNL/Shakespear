from django.forms import Form, ValidationError
from django.forms.fields import CharField, EmailField

from Questionaire.models import InquiryQuestionAnswer, Score
from inquirer_settings.models import PendingMailVerifyer
from questionaire_mailing.models import TriggeredMailTask


class RemoveInquiryDataForm(Form):
    def __init__(self, *args, inquiry=None, **kwargs):
        assert inquiry is not None
        self.inquiry = inquiry

        super(RemoveInquiryDataForm, self).__init__(*args, **kwargs)

    def delete(self):
        # Delete all related data
        InquiryQuestionAnswer.objects.filter(
            inquiry=self.inquiry,
        ).delete()

        Score.objects.filter(
            inquiry=self.inquiry
        ).delete()

        # Todo, write test


class EmailForm(Form):
    """ A form that requests the mail for an inquirer object """
    email = EmailField()
    confirm_mail_send = False

    def __init__(self, *args, inquirer=None, **kwargs):
        assert inquirer is not None
        self.inquirer = inquirer

        super(EmailForm, self).__init__(*args, **kwargs)

        # Set the initial e-mail address, the pending one if one is pending, otherwise the affirmed one
        email = PendingMailVerifyer.objects.filter(
            inquirer=self.inquirer,
            active=True,
        ).first()
        if email is None:
            email = inquirer.email
        else:
            email = email.email

        self.fields['email'].initial = email

    def save(self, **kwargs):
        email = self.cleaned_data['email']

        if email is None or "":
            # Clear the email
            self.inquirer.email = ""
            self.inquirer.email_validated = False
            self.inquirer.save()

            # Ensure there are no other pending mail adresses active for this Inquirer
            PendingMailVerifyer.objects.filter(inquirer=self.inquirer).update(active=False)
            return

        if self.inquirer.email != email:
            # Mail address has changed

            # Seek a pending mail validation object
            try:
                pending_mail = PendingMailVerifyer.objects.get(
                    inquirer=self.inquirer,
                    email=email
                )
                if pending_mail.is_verified:
                    self.inquirer.email = email
                    self.inquirer.save()
                    self.confirm_mail_send = False
                    return
                if pending_mail.active:
                    return

                # There is no acitve pending thing with this e-mail account
                self.create_instance_and_send_mail(email)

            except PendingMailVerifyer.DoesNotExist:
                self.create_instance_and_send_mail(email)

    def create_instance_and_send_mail(self, email):
        # NOTE: Upon PendingMailVerifyer object creation it automatically deactivates any active PMV for this inquirer
        # So there is always at most 1 PMV active at the same time
        PendingMailVerifyer.objects.create(
            inquirer=self.inquirer,
            email=email,
        )
        self.confirm_mail_send = True

        TriggeredMailTask.trigger(
            TriggeredMailTask.TRIGGER_MAIL_CHANGED,
            inquirer=self.inquirer,
            email=email,
        )


class PendingMailForm(Form):
    code = CharField(required=True)
    email = CharField(required=True)

    def clean(self):
        cleaned_data = super(PendingMailForm, self).clean()

        if cleaned_data.get('code', None):
            try:
                self.instance = PendingMailVerifyer.objects.get(code=cleaned_data['code'])
            except PendingMailVerifyer.DoesNotExist:
                raise ValidationError(
                    'Gegevens van email validatie komen niet overeen.',
                    code='invalid',
                    params={},
                )

            if self.instance.email != cleaned_data['email']:
                raise ValidationError(
                    'Gegevens van email validatie komen niet overeen.',
                    code='invalid',
                    params={},
                )

            if self.instance.is_verified:
                raise ValidationError(
                    'Mail is al gevalideerd',
                    code='already_validated',
                    params={},
                )

            if not self.instance.active:
                raise ValidationError(
                    'Deze email verificatie link is niet meer actief. Mogelijk dat de gebruiker het e-mail adres heeft '
                    'aangepast.',
                    code='not_active',
                    params={},
                )

    def verify(self):
        self.instance.verify()


class ResendPendingMailForm(Form):
    """
    Form that resends the e-mail for a pending email confirmation
    """

    def __init__(self, *args, inquirer=None, **kwargs):
        assert inquirer is not None
        self.inquirer=inquirer
        super(ResendPendingMailForm, self).__init__(*args, **kwargs)

    def clean(self):
        pending_mails = PendingMailVerifyer.objects.filter(inquirer=self.inquirer, active=True)
        if pending_mails.count() == 0:
            raise ValidationError("There are no pending e-mails")

        if pending_mails.count() > 1:
            raise RuntimeError(f"There were multiple active pending mails for {self.inquirer.id}")

    def send(self):
        """ Send the verification mail again """
        pending_mail = PendingMailVerifyer.objects.filter(inquirer=self.inquirer, active=True).last()

        TriggeredMailTask.trigger(
            TriggeredMailTask.TRIGGER_MAIL_CHANGED,
            inquirer=self.inquirer,
            email=pending_mail.email,
        )
