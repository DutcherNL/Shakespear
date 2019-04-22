from django import forms
from .models import PageEntry, Inquiry

from .fields import QuestionFieldFactory


class QuestionPageForm(forms.Form):
    """
    The Form presenting all questions on a page
    """

    def __init__(self, page, inquiry, *args, **kwargs):
        super(QuestionPageForm, self).__init__(*args, **kwargs)
        self.page = page

        for entry in PageEntry.objects.filter(page=page).order_by('position'):
            question = entry.question
            field = QuestionFieldFactory.get_field_by_model(question, inquiry=inquiry)

            self.fields[question.name] = field
            field.backward(inquiry)

    def save(self, inquiry):

        if inquiry is int:
            inquiry = Inquiry.objects.get(id=inquiry)

        for key, value in self.cleaned_data.items():
            self.fields[key].save(value, inquiry)

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


