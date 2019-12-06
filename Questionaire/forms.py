from django import forms
from .models import PageEntry, Inquirer, Inquiry

from .fields import FieldFactory, QuestionFieldMixin, IgnorableEmailField
from mailing.forms import MailForm
from mailing.mails import send_templated_mail


class QuestionPageForm(forms.Form):
    """
    The Form presenting all questions on a page
    """

    def __init__(self, page, inquiry, *args, **kwargs):
        super(QuestionPageForm, self).__init__(*args, **kwargs)
        self.page = page

        for entry in PageEntry.objects.filter(page=page).order_by('position'):
            field = FieldFactory.get_field_by_entrymodel(entry, inquiry=inquiry)
            if isinstance(field, QuestionFieldMixin):
                field.backward(inquiry)

            self.fields[field.name] = field

    def save(self, inquiry, save_raw=False):
        if inquiry is int:
            inquiry = Inquiry.objects.get(id=inquiry)

        if save_raw:
            # Save the raw uncleaned data. Used when using the back button
            for name, field in self.fields.items():
                # value_from_datadict() gets the data from the data dictionaries.
                # Each widget type knows how to retrieve its own data, because some
                # widgets split data over several HTML fields.
                value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
                field.save(value, inquiry)

        else:
            if self.is_valid():
                for key, value in self.cleaned_data.items():
                    self.fields[key].save(value, inquiry)

        # Save the inquiry, aka update that it has changed
        inquiry.save()

    def forward(self, inquiry):
        """
        Compute the effects of the form, works in the assumption it is not yet completed.
        :return:
        """
        # For each question in this form
        # Process the anwers

        # Loop over all questions in this form
        for field in self.fields.values():
            field.forward(inquiry)
            pass

    def backward(self, inquiry):
        """
        Compute the effects of the form, works in the assumption it is not yet completed.
        :return:
        """
        # For each question in this form
        # Process the anwers

        # Loop over all questions in this form
        for field in self.fields.values():
            field.backward(inquiry)
            pass


class EmailForm(forms.Form):
    email = IgnorableEmailField(required=False)

    def __init__(self, *args, inquirer=None, **kwargs):
        if inquirer is None:
            raise KeyError("inquiry is missing or is None")

        self.inquirer = inquirer
        return super(EmailForm, self).__init__(*args, **kwargs)

    def save(self):
        self.inquirer.email = self.cleaned_data.get('email', None)
        self.inquirer.save()

        subject = "Welkom bij de menukaart"
        template = "questionaire/welcome_code"
        context = {'code': self.inquirer.get_inquiry_code()}

        send_templated_mail(subject=subject,
                            template_name=template,
                            context_data=context,
                            recipient=self.inquirer.email)


class InquiryLoadDebugForm(forms.Form):
    code = forms.CharField(max_length=6)
    inquiry_model = None

    def clean(self):
        cleaned_data = super(InquiryLoadDebugForm, self).clean()

        code = cleaned_data.get('code')

        if code is not None:
            try:
                self.inquiry_model = Inquiry.get_inquiry_model_from_code(code)
            except Inquiry.DoesNotExist:
                raise forms.ValidationError("Code is incorrect. Inquiry is not known")

        return cleaned_data

    def get_inquiry(self):
        if self.inquiry_model is None:
            raise ValueError("No inquiry model computed yet")

        return self.inquiry_model


class InquirerLoadForm(forms.Form):
    code = forms.CharField(max_length=6, required=True)
    email = forms.EmailField(required=False)
    inquirer_model = None

    def __init__(self, *args, exclude=[], **kwargs):
        super(InquirerLoadForm, self).__init__(*args, **kwargs)
        if 'email' in exclude:
            self.fields.pop('email')

    def clean(self):
        cleaned_data = super(InquirerLoadForm, self).clean()

        code = cleaned_data.get('code')

        if code is not None:
            try:
                self.inquirer_model = Inquirer.get_inquiry_model_from_code(code)
            except Inquirer.DoesNotExist:
                raise forms.ValidationError("Code is incorrect. Inquiry is not known")

            if self.inquirer_model.email is not None:
                if self.cleaned_data.get('email', None) != self.inquirer_model.email:
                    raise forms.ValidationError("Dit is niet het geaccosieerde e-mail adres")

        return cleaned_data

    def get_inquiry(self):
        if self.inquirer_model is None:
            raise ValueError("No inquirer model computed yet")

        return self.inquirer_model.active_inquiry

    def get_code_value(self):
        return self.cleaned_data['code']


class InquiryMailForm(MailForm):

    def __init__(self, *args, **kwargs):
        super(InquiryMailForm, self).__init__(*args, **kwargs)
        self.fields['to'].disabled = True