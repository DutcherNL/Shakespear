from django.forms import CharField, IntegerField, DecimalField, ChoiceField
from django.core.exceptions import ObjectDoesNotExist
import ast

from .models import InquiryQuestionAnswer, AnswerOption, TechnologyScore, StoredVariable


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
            choices = [(0, '---')]

            for answer in question.answeroption_set.order_by("value"):
                choices.append((answer.value, answer.answer))

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
        if not self.is_empty_value(value):
            inquiry_question_answer_obj = InquiryQuestionAnswer.objects.get_or_create(question=self.question, inquiry=inquiry)[0]
            if inquiry_question_answer_obj.answer != value:
                # Answer has changed
                inquiry_question_answer_obj.answer = value
                inquiry_question_answer_obj.processed_answer = self.get_answer_option(value)
                inquiry_question_answer_obj.save()

            for stored_variable in self.question.answervariable_set.all():
                # Todo, processing according to processing input
                StoredVariable.objects.get_or_create(name=stored_variable.name, value=value)

        else:
            inquiry_question_answer_obj_query = InquiryQuestionAnswer.objects.filter(question=self.question, inquiry=inquiry)
            if inquiry_question_answer_obj_query.exists():
                # Revert the scoring if that has been processed
                if inquiry_question_answer_obj_query[0].processed:
                    inquiry_question_answer_obj_query[0].backward(inquiry)

                InquiryQuestionAnswer.objects.filter(question=self.question, inquiry=inquiry).delete()

    def get_answer_option(self, value):
        return None

    def is_empty_value(self, value):
        """
        Returns whether the given value is identified as an empty answer
        :param value: the given answer
        :return: whether the given entry is empty for this parameter
        """
        return value is None or value == 0

    def forward(self, inquiry):
        """
        Computes the effects on the inquiry in a forwards motion
        :return:
        """
        try:
            inquiry_answer = InquiryQuestionAnswer.objects.get(inquiry=inquiry, question=self.question)
        except ObjectDoesNotExist:
            # If the object does not exist yet, which can happen when no answer is given
            return


        if inquiry_answer.processed:
            return
        answer_option = inquiry_answer.processed_answer

        if answer_option is not None:
            for adjustment in answer_option.answerscoring_set.all():
                tech_score = TechnologyScore.objects.get_or_create(technology=adjustment.technology, inquiry=inquiry)[0]
                tech_score.usefulness_score += adjustment.usefulness_change
                tech_score.importance_score += adjustment.importance_change
                tech_score.save()

            inquiry_answer.processed = True
            inquiry_answer.save()

    def backward(self, inquiry):
        """
        Reverts the effects on the inquiry in a forwards motion
        :return:
        """
        try:
            inquiry_answer = InquiryQuestionAnswer.objects.get(inquiry=inquiry, question=self.question)
        except ObjectDoesNotExist:
            # If the object does not exist yet, which is the case on empty answers
            return

        if not inquiry_answer.processed:
            return

        answer_option = inquiry_answer.processed_answer

        if answer_option is not None:
            for adjustment in answer_option.answerscoring_set.all():
                tech_score = TechnologyScore.objects.get_or_create(technology=adjustment.technology, inquiry=inquiry)[0]
                tech_score.usefulness_score -= adjustment.usefulness_change
                tech_score.importance_score -= adjustment.importance_change
                tech_score.save()

            inquiry_answer.processed = False
            inquiry_answer.save()


class CharQuestionField(QuestionFieldMixin, CharField):
    def is_empty_value(self, value):
        return value is None or value == ""


class IntegerQuestionField(QuestionFieldMixin, IntegerField):
    pass


class DecimalQuestionField(QuestionFieldMixin, DecimalField):
    pass


class ChoiceQuestionField(QuestionFieldMixin, ChoiceField):

    def get_answer_option(self, value):
        """
        Returns the answer_option for the given value
        :param value: The value of the answer
        :return:
        """
        if int(value) is 0:
            return None
        else:
            return AnswerOption.objects.get(question=self.question, value=int(value))




