from django import forms
from .models import PageEntry, Inquirer, Inquiry, Question, InquiryQuestionAnswer

from mailing.forms import MailForm
from mailing.mails import send_templated_mail

from .fields import QuestionFieldFactory, QuestionFieldMixin, IgnorableEmailField


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

    def save(self, inquiry, save_raw=False):
        if not save_raw and not self.is_valid():
            # Current state can't be saved as it is not valid
            return

        for question in self.questions:
            name = question.name

            if save_raw:
                # Save the raw uncleaned data, as uncleaned data is not stored, re-retrieve it from the fields widget
                answer = self.fields[name].widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
                question.answer_for_inquiry(inquiry, answer, False)
            else:
                # Answer the question normally
                answer = self.cleaned_data[name]
                question.answer_for_inquiry(inquiry, answer, True)

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