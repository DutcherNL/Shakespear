from django.forms import CharField, IntegerField, DecimalField, ChoiceField, Field
from .widgets import CustomRadioSelect, InformationDisplayWidget, IgnorableInput, ExternalDataInputLocal
from .models import ExternalQuestionSource
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator

from string import Formatter
import ast

from .models import InquiryQuestionAnswer, AnswerOption, Score


class FieldFactory:
    """
    Factory class generating fields from Question model instances
    """

    @staticmethod
    def get_field_by_entrymodel(entry, inquiry=None):
        if entry.entry_type == 1:
            return InformationField(entry.pageentrytext, inquiry=inquiry)
        elif entry.entry_type == 2:
            peq = entry.pageentryquestion
            return FieldFactory.get_field_by_questionmodel(peq.question, inquiry=inquiry, required=peq.required)

    @staticmethod
    def get_field_by_questionmodel(question, inquiry=None, required=False):
        q_type = question.question_type

        # Todo: implement validators with field.validators

        if q_type == 0:
            # Text question
            return CharQuestionField(question, inquiry, required=required)
        if q_type == 1:
            # Integer question
            return IntegerQuestionField(question, inquiry, required=required)
        if q_type == 2:
            # Double question
            return DecimalQuestionField(question, inquiry, required=required)
        if q_type == 3:
            # Multiple choice question
            return ChoiceQuestionField(question, inquiry, required=required)

        raise ValueError("q_type is beyond expected range")


class QuestionFieldMixin:
    def __init__(self, question, inquiry, *args, **kwargs):
        if ExternalQuestionSource.objects.filter(question=question).exists():
            self.widget = ExternalDataInputLocal(inquiry, question.externalquestionsource)

        super().__init__(*args, **kwargs)
        self.question = question
        self.name = question.name
        self.label = question.question_text

        if self.question.help_text:
            self.help_text = self.question.help_text

        if inquiry is not None:
            answer_obj = InquiryQuestionAnswer.objects.filter(question=question, inquiry=inquiry)
            if answer_obj.exists():
                self.initial = answer_obj.first().answer

        self.validators = [*self.validators, *self.construct_validators()]

    def clean(self, value, ignore_required=False):
        return  super().clean(value)

    def construct_validators(self):
        validator_dict = self.get_question_options()
        validators = []

        keys = validator_dict.keys()

        if 'regex' in keys:
            regex = validator_dict.get('regex')
            message = "Please type a normal value"
            if 'regex_message' in keys:
                message = validator_dict.get('regex_message')
            validators.append(RegexValidator(regex=regex, message=message))

        return validators

    def get_question_options(self):
        return ast.literal_eval(self.question.options)

    def save(self, value, inquiry):
        if not self.is_empty_value(value):
            inquiry_question_answer_obj = InquiryQuestionAnswer.objects.get_or_create(question=self.question, inquiry=inquiry)[0]
            if inquiry_question_answer_obj.answer != value:
                # Answer has changed
                # Todo: Check if a check on processing needs to be placed here
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
    widget = IgnorableInput

    def is_empty_value(self, value):
        return value is None or value == ""

    def get_answer_option(self, value):
        try:
            if not self.is_empty_value(value):
                return AnswerOption.objects.get(question=self.question, answer="NotNone")
        except AnswerOption.DoesNotExist:
            return None


class IntegerQuestionField(QuestionFieldMixin, IntegerField):
    def get_answer_option(self, value):
        if value is None:
            return None

        options = AnswerOption.objects.filter(question=self.question)

        best_option = None
        best_value = -9999999
        for option in options:
            answer_value = int(option.answer)
            if best_value < answer_value <= value:
                best_value = answer_value
                best_option = option

        return best_option


class DecimalQuestionField(QuestionFieldMixin, DecimalField):
    pass


class ChoiceQuestionField(QuestionFieldMixin, ChoiceField):
    widget = CustomRadioSelect

    def __init__(self, question, inquiry, *args, **kwargs):
        super(ChoiceQuestionField, self).__init__(question, inquiry, *args, **kwargs)

        choices = []
        images = {}

        for answer in question.answeroption_set.order_by("value"):
            choices.append((answer.value, answer.answer))
            if answer.image:
                images[answer.value] = answer.image

        self.choices = choices
        self.widget.images = images

        question_options = self.get_question_options()
        if 'height' in question_options.keys():
            self.widget.answer_height = question_options['height']

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


class LookUpQuestion(QuestionFieldMixin, CharField):
    widget = CharField(required=False)

    def __init__(self, question, inquiry, *args, **kwargs):
        super(LookUpQuestion, self).__init__(question, inquiry, *args, **kwargs)


class InformationField(Field):
    widget = InformationDisplayWidget

    def __init__(self, page_entry_obj, *args, inquiry=None, **kwargs):
        super(InformationField, self).__init__(*args, **kwargs)
        self.name = "-- sample_name --"
        self.text = self.prep_text(page_entry_obj.text, inquiry=inquiry)
        self.label = ""
        self.required = False
        self.initial = self.text

    def save(self, *args, **kwargs):
        pass

    def forward(self, *args, **kwargs):
        pass

    def backward(self, *args, **kwargs):
        pass

    def prep_text(self, text, inquiry=None):
        formatter = Formatter()
        iter_obj = formatter.parse(text)
        keys = []
        for literal, key, format, conversion in iter_obj:
            keys.append(key)

        format_dict = {}
        for key in keys:
            if key is None:
                continue

            if key.startswith('q_'):
                iqa_obj = InquiryQuestionAnswer.objects.get(question__name=key[2:], inquiry=inquiry)
                format_dict[key] = iqa_obj.get_readable_answer()
            elif key.startswith('v_'):
                score_obj = Score.objects.get(declaration__name=key[2:], inquiry=inquiry)
                format_dict[key] = score_obj.score

        return text.format(**format_dict)