from django import forms
from .models import PageEntry
import ast


class QuestionFieldFactory:
    """
    Factory class generating fields from Question model instances
    """

    @staticmethod
    def get_field_by_model(question, inquiry=None):
        q_type = question.question_type

        if q_type == 0:
            # Text question
            limits = ast.literal_eval(question.validators)
            return forms.CharField(label=question.question_text, **limits)
        if q_type == 1:
            # Integer question
            limits = ast.literal_eval(question.validators)
            return forms.IntegerField(**limits)
        if q_type == 2:
            # Double question
            return forms.DecimalField()
        if q_type == 3:
            # Choice question
            choices = (
                (0, 'A'),
                (1, 'B'),
                (2, 'C'),
                (3, 'D'),
            )
            return forms.ChoiceField(choices=choices)

        raise ValueError("q_type is beyond expected range")


class QuestionPageForm(forms.Form):
    """
    The Form presenting all questions on a page
    """

    def __init__(self, page, *args, **kwargs):
        super(QuestionPageForm, self).__init__(*args, **kwargs)

        for entry in PageEntry.objects.filter(page=page).order_by('position'):
            question = entry.question
            field = QuestionFieldFactory.get_field_by_model(question)

            self.fields[question.name] = field

