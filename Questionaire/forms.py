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

    def clean(self):
        cleaned_data = super(QuestionPageForm, self).clean()
        return cleaned_data

    def save(self, inquiry):
        self.clean()

        if inquiry is int:
            inquiry = Inquiry.objects.get(id=inquiry)

        for key, value in self.cleaned_data.items():
            self.fields[key].save(value, inquiry)


