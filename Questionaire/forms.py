from django import forms

from mailing.forms import MailForm
from inquirer_settings.models import PendingMailVerifyer

from .models import PageEntry, Inquirer, Question, InquiryQuestionAnswer
from .fields import QuestionFieldFactory, IgnorableEmailField
from .widgets import SimpleBootstrapCheckBox

from questionaire_mailing.models import TriggeredMailTask


class QuestionPageForm(forms.Form):
    """
    The Form presenting all questions on a page
    """

    def __init__(self, *args, page=None, inquiry=None, **kwargs):
        super(QuestionPageForm, self).__init__(*args, **kwargs)
        self.page = page
        self.questions = Question.objects.filter(pageentryquestion__page=page)

        # Get all page entries and transform them to a field
        for entry in PageEntry.objects.filter(page=page).order_by('position'):
            field = QuestionFieldFactory.get_field_by_entrymodel(entry, inquiry=inquiry)

            self.fields[field.name] = field

        self.backward(inquiry)

    def _save_raw(self, question, inquiry):
        """ Saves a certain question in a raw format"""
        answer = self.fields[question.name].widget.value_from_datadict(self.data,
                                                                       self.files,
                                                                       self.add_prefix(question.name))
        question.answer_for_inquiry(inquiry, answer, False)

    def _save_clean(self, question, inquiry):
        """ Saves a certain question with cleaned data"""
        answer = self.cleaned_data[question.name]
        question.answer_for_inquiry(inquiry, answer, True)

    def save(self, inquiry, save_raw=False):
        if not save_raw and not self.is_valid():
            # Current state can't be saved as it is not valid
            return

        # Note: The current deconstred process is to ready for a future implemenation where this process is threaded
        # However, I could not implement this locally without changing the database to e.g. Postgres due to table-locks
        # occuring in the test case and thus failing.

        # Select the correct method to save the data (raw, or clean
        if save_raw:
            save_method = self._save_raw
        else:
            save_method = self._save_clean

        # Save all questions
        for question in self.questions:
            save_method(question, inquiry)

        # Update the inquiry itself (to adjust the last_visited time
        inquiry.save()

    def forward(self, inquiry):
        """
        Process all questions in a forward manner
        :return:
        """
        # For each question in this form
        # Process the anwers

        # Loop over all questions in this form
        for question in self.questions:
            try:
                inquiry_answer = InquiryQuestionAnswer.objects.get(inquiry=inquiry, question=question)
                inquiry_answer.forward()
            except InquiryQuestionAnswer.DoesNotExist:
                # If the object does not exist yet, which is the case on empty answers
                continue

    def backward(self, inquiry):
        """
        Process all questions in a backwards manner
        :return:
        """

        # Loop over all questions in this form
        for question in self.questions:
            try:
                inquiry_answer = InquiryQuestionAnswer.objects.get(inquiry=inquiry, question=question)
                inquiry_answer.backward()
            except InquiryQuestionAnswer.DoesNotExist:
                # If the object does not exist yet, which is the case on empty answers
                continue


class EmailForm(forms.Form):
    """ A form that requests the mail for an inquirer object """
    email = IgnorableEmailField(required=False)

    def __init__(self, *args, inquirer=None, **kwargs):
        if inquirer is None:
            raise KeyError("inquirer is missing or is None")

        self.inquirer = inquirer
        return super(EmailForm, self).__init__(*args, **kwargs)

    def save(self):
        email = self.cleaned_data.get('email', None)
        if email:
            PendingMailVerifyer.objects.create(
                inquirer=self.inquirer,
                email=email,
            )
            # Store the mail, but do not confirm it as validated
            self.inquirer.email = email
            self.inquirer.email_validated = False
            self.inquirer.save()

            TriggeredMailTask.trigger(
                TriggeredMailTask.TRIGGER_MAIL_REGISTERED,
                inquirer=self.inquirer,
                email=email,
            )


class CreateInquirerForm(forms.ModelForm):
    accept_cookies = forms.BooleanField(
        required=True,
        label="Ik ga akkoord met het gebruik van cookies",
        widget=SimpleBootstrapCheckBox,
    )
    accept_privacy = forms.BooleanField(
        required=True,
        label="Ik ga akkoord met het privacy beleid",
        widget=SimpleBootstrapCheckBox,
    )

    class Meta:
        model = Inquirer
        fields = ['accept_cookies', 'accept_privacy']


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

        if email == "":
            raise forms.ValidationError("Er is een e-mail adres aan deze vragenlijst gekoppeld. \n"
                                        "Gelieve dit in te vullen zodat wij weten dat u het bent")

        raise forms.ValidationError("Dit is niet het geaccosieerde e-mail adres")

    def get_inquiry(self):
        if self.inquirer_model is None:
            raise ValueError("No inquirer model computed yet")

        return self.inquirer_model.active_inquiry


class InquiryMailForm(MailForm):

    def __init__(self, *args, **kwargs):
        super(InquiryMailForm, self).__init__(*args, **kwargs)
        self.fields['to'].disabled = True