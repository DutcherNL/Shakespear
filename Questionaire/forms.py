from django import forms
from .models import PageEntry, Inquirer, Inquiry

from .fields import QuestionFieldFactory, QuestionFieldMixin, IgnorableEmailField
from mailing.forms import MailForm
from mailing.mails import send_templated_mail


class QuestionPageForm(forms.Form):
    """
    The Form presenting all questions on a page
    """

    def __init__(self, page, inquiry, *args, **kwargs):
        super(QuestionPageForm, self).__init__(*args, **kwargs)
        self.page = page

        # Get all page entries and transform them to a field
        for entry in PageEntry.objects.filter(page=page).order_by('position'):
            field = QuestionFieldFactory.get_field_by_entrymodel(entry, inquiry=inquiry)
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
    """ A form that requests the mail for an inquirer object """
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


class InquirerLoadForm(forms.Form):
    """ Form that attemps to retrieve an inquirer model based on the key and the e-mail adres """
    code = forms.CharField(max_length=6, required=True)
    email = forms.EmailField(required=False)
    inquirer_model = None

    def __init__(self, *args, exclude=[], **kwargs):
        super(InquirerLoadForm, self).__init__(*args, **kwargs)
        if 'email' in exclude:
            self.fields.pop('email')

    @property
    def inquirer_model(self):
        try:
            code = self.cleaned_data.get('code')
            if code is None:
                return None
            return Inquirer.get_inquiry_model_from_code(code)
        except Inquirer.DoesNotExist:
            return None

    def clean_code(self):
        """ Clean the code """
        if self.inquirer_model is None:
            raise forms.ValidationError("Code is incorrect. Inquiry is not known")

        return self.cleaned_data.get('code')

    def clean_email(self):
        """ Clean the email, check if it matches the inquiry object """
        email = self.cleaned_data.get('email')
        if self.inquirer_model is None:
            return email

        if self.inquirer_model.email is None:
            # If email should be empty, check if it is empty
            if email == "":
                return email
        elif email == self.inquirer_model.email:
            # There is an email left, validate it
            return email

        raise forms.ValidationError("Dit is niet het geaccosieerde e-mail adres")

    def get_inquiry(self):
        if self.inquirer_model is None:
            raise ValueError("No inquirer model computed yet")

        return self.inquirer_model.active_inquiry


class InquiryMailForm(MailForm):

    def __init__(self, *args, **kwargs):
        super(InquiryMailForm, self).__init__(*args, **kwargs)
        self.fields['to'].disabled = True