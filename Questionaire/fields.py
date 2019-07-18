from django.forms import CharField, IntegerField, DecimalField, ChoiceField, Field
from django.forms.widgets import RadioSelect, NumberInput
from .widgets import CustomRadioSelect, InformationDisplayWidget
from django.core.exceptions import ObjectDoesNotExist
import ast

from .models import InquiryQuestionAnswer, AnswerOption, Score


class FieldFactory:
    """
    Factory class generating fields from Question model instances
    """

    @staticmethod
    def get_field_by_entrymodel(entry, inquiry=None):
        if entry.entry_type == 1:
            return InformationField(entry.pageentrytext)
        elif entry.entry_type == 2:
            peq = entry.pageentryquestion
            return FieldFactory.get_field_by_questionmodel(peq.question, inquiry=inquiry, required=peq.required)

    @staticmethod
    def get_field_by_questionmodel(question, inquiry=None, required=False):
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
            # Multiple choice question
            return ChoiceQuestionField(question, inquiry, required=required)

        raise ValueError("q_type is beyond expected range")


class QuestionFieldMixin:

    def __init__(self, question, inquiry, *args, required=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        self.name = question.name
        self.label = question.question_text
        self.required = required
        print("Init QFM")
        if inquiry is not None:
            answer_obj = InquiryQuestionAnswer.objects.filter(question=question, inquiry=inquiry)
            print("Set initial?")
            if answer_obj.exists():
                self.initial = answer_obj.first().answer
                print("Initial set: {0}".format(self.initial))

    def save(self, value, inquiry):
        if not self.is_empty_value(value):
            inquiry_question_answer_obj = InquiryQuestionAnswer.objects.get_or_create(question=self.question, inquiry=inquiry)[0]
            if inquiry_question_answer_obj.answer != value:
                # Answer has changed
                inquiry_question_answer_obj.answer = value
                inquiry_question_answer_obj.processed_answer = self.get_answer_option(value)
                inquiry_question_answer_obj.save()

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
                score_obj = Score.objects.get_or_create(declaration=adjustment.declaration, inquiry=inquiry)[0]
                adjustment.adjust_score(score_obj)
                score_obj.save()

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
                score_obj = Score.objects.get_or_create(declaration=adjustment.declaration, inquiry=inquiry)[0]
                adjustment.adjust_score(score_obj, revert=True)
                score_obj.save()

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
    widget = CustomRadioSelect

    def __init__(self, question, inquiry, *args, **kwargs):
        super(ChoiceQuestionField, self).__init__(question, inquiry, *args, **kwargs)

        choices = []

        for answer in question.answeroption_set.order_by("value"):
            choices.append((answer.value, answer.answer))

        self.choices = choices
        self.required = False

    def get_answer_option(self, value):
        """
        Returns the answer_option for the given value
        :param value: The value of the answer
        :return:
        """
        if value is None or value == '':
            return None
        else:
            return AnswerOption.objects.get(question=self.question, value=int(value))


class InformationField(Field):
    widget = InformationDisplayWidget

    def __init__(self, page_entry_obj, *args, **kwargs):
        super(InformationField, self).__init__(*args, **kwargs)
        self.name = "-- sample_name --"
        self.text = page_entry_obj.text
        self.label = ""
        self.required = False
        self.initial = self.text

    def save(self, *args, **kwargs):
        pass

    def forward(self, *args, **kwargs):
        pass

    def backward(self, *args, **kwargs):
        pass