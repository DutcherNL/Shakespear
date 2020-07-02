from django.forms import Form, ValidationError
from django.forms.fields import CharField, EmailField

from Questionaire.models import InquiryQuestionAnswer, Score
from inquirer_settings.models import PendingMailVerifyer


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

        self.fields['email'].initial = inquirer.email

    def save(self, **kwargs):
        email = self.cleaned_data['email']

        if self.inquirer.email != email:
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
                self.create_instance_and_send_mail()

            except PendingMailVerifyer.DoesNotExist:
                self.create_instance_and_send_mail

    def create_instance_and_send_mail(self, email):
        PendingMailVerifyer.objects.create(
            inquirer=self.inquirer,
            email=email,
        )
        self.confirm_mail_send = True
        # Todo send mail


class PendingMailForm(Form):
    code = CharField()
    email = CharField()

    def clean(self):
        cleaned_data = super(PendingMailForm, self).clean()

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


