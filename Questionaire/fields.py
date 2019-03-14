from django.forms import CharField, IntegerField, DecimalField, ChoiceField
import ast

from .models import InquiryQuestionAnswer


class QuestionFieldFactory:
    """
    Factory class generating fields from Question model instances
    """

    @staticmethod
    def get_field_by_model(question, inquiry=None):
        q_type = question.question_type

        # Todo: implement validators with field.validators

        if q_type == 0:
            # Text question
            limits = ast.literal_eval(question.validators)
            return CharQuestionField(question, inquiry, **limits)
        if q_type == 1:
            # Integer question
            limits = ast.literal_eval(question.validators)
            return IntegerQuestionField(question, inquiry, **limits)
        if q_type == 2:
            # Double question
            return DecimalQuestionField(question, inquiry)
        if q_type == 3:
            # Choice question
            choices = (
                (1, 'A'),
                (2, 'B'),
                (3, 'C'),
                (4, 'D'),
            )
            return ChoiceQuestionField(question, inquiry, choices=choices)

        raise ValueError("q_type is beyond expected range")


class QuestionFieldMixin:

    def __init__(self, question, inquiry, *args, required=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        self.label = question.question_text
        self.required = required
        if inquiry is not None:
            answer_obj = InquiryQuestionAnswer.objects.filter(question=question, inquiry=inquiry)
            if answer_obj.exists():
                self.initial = answer_obj.first().answer

    def save(self, value, inquiry):
        if is_empty_value(value):
            answer = InquiryQuestionAnswer.objects.get_or_create(question=self.question, inquiry=inquiry)[0]
            answer.answer = value
            answer.save()
        else:
            if InquiryQuestionAnswer.objects.filter(question=self.question, inquiry=inquiry).exists():
                InquiryQuestionAnswer.objects.filter(question=self.question, inquiry=inquiry).delete()

    def is_empty_value(self, value):
        """
        Returns whether the given value is identified as an empty answer
        :param value: the given answer
        :return: whether the given entry is empty for this parameter
        """
        return value is None or value != 0


class CharQuestionField(QuestionFieldMixin, CharField):
    def is_empty_value(self, value):
        return value is None or value == ""


class IntegerQuestionField(QuestionFieldMixin, IntegerField):
    pass


class DecimalQuestionField(QuestionFieldMixin, DecimalField):
    pass


class ChoiceQuestionField(QuestionFieldMixin, ChoiceField):
    pass