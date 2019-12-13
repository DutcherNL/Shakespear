from django.forms import CharField, IntegerField, DecimalField, ChoiceField, Field, ValidationError, EmailField
from .widgets import CustomRadioSelect, InformationDisplayWidget,\
    IgnorableInput, ExternalDataInputLocal, IgnorableInputMixin, IgnorableEmailInput
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator

from string import Formatter
import ast

from .models import ExternalQuestionSource, InquiryQuestionAnswer, AnswerOption, Score, Question


class QuestionFieldFactory:
    """ Factory class generating fields from Question model instances

    It creates customised form fields based on the type of page entry added
    """

    @staticmethod
    def get_field_by_entrymodel(entry, inquiry=None):
        """
        Returns an initiated field based on the entry type
        :param entry: The PageEntry object (as defined in Questionaire.models)
        :param inquiry: The inquiry object (can be left out to generate blank questions)
        :return: An initiated Field instance
        """
        if entry.entry_type == 1:
            return InformationField(entry.pageentrytext, inquiry=inquiry)
        elif entry.entry_type == 2:
            peq = entry.pageentryquestion
            return QuestionFieldFactory.get_field_by_questionmodel(peq.question, inquiry=inquiry, required=peq.required)

    @staticmethod
    def get_field_by_questionmodel(question, inquiry=None, required=False):
        """
        Returns an initiated QuestionField based on the question entered
        :param question: The question object
        :param inquiry: The inquiry object
        :param required: Whether the field should be required, defaults to false
        :return:
        """
        q_type = question.question_type

        # Todo: implement validators with field.validators

        if q_type == Question.TYPE_OPEN:
            # Text question
            return CharQuestionField(question, inquiry, required=required)
        if q_type == Question.TYPE_INT:
            # Integer question
            return IntegerQuestionField(question, inquiry, required=required)
        if q_type == Question.TYPE_DOUBLE:
            # Double question
            return DecimalQuestionField(question, inquiry, required=required)
        if q_type == Question.TYPE_CHOICE:
            # Multiple choice question
            return ChoiceQuestionField(question, inquiry, required=required)

        raise ValueError("q_type is beyond expected range")


class IgnorableFieldCheckMixin:
    """ A mixin that takes the IgnorableInput nature from the mixin into account
    Below each question there is an option to leave the question empty
    """

    def validate(self, value):
        super().validate(value)
        # Check if the widget is ignorable. If so, check if it has been answered with the non-answer option
        if isinstance(self.widget, IgnorableInputMixin):
            if (value is None or value == '') and not self.widget.is_answered:
                raise ValidationError("Deze vraag is nog niet beantwoord ", code='required')


class QuestionFieldMixin:
    """ Mixin class for Question Fields

    Takes care of general information and update behaviour as well as introducing the forward() and backward() methods

    :param question: the question object
    """

    def __init__(self, question, inquiry, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if ExternalQuestionSource.objects.filter(question=question).exists():
            # Check if the input of this question should come from elsewhere, if so replace the widget
            self.widget = ExternalDataInputLocal(inquiry, question.externalquestionsource)

        # Set the local attributes
        self.question = question
        self.name = question.name
        self.label = question.question_text

        # If the question has a help text, store it in the field as well
        if self.question.help_text:
            self.help_text = self.question.help_text

        if inquiry is not None:
            # If an inquiry is given, get the answer stored for that inquiry
            answer_obj = InquiryQuestionAnswer.objects.filter(question=question, inquiry=inquiry)
            if answer_obj.exists():
                self.initial = answer_obj.first().answer
            else:
                # There is no answer, set the widget to empty (used for ignored widgets)
                self.widget.empty = True

        # Store the validators
        self.validators = [*self.validators, *self.construct_validators()]

    def clean(self, value, ignore_required=False):
        return super().clean(value)

    def construct_validators(self):
        """
        Constructs and returns the validators for the question
        :return: A list of validators
        """
        validator_dict = self.get_question_options()
        validators = []

        keys = validator_dict.keys()

        # There is a regex validator
        if 'regex' in keys:
            regex = validator_dict.get('regex')
            message = "Please type a normal value"
            # Check if a custom regex message is present
            if 'regex_message' in keys:
                message = validator_dict.get('regex_message')
            validators.append(RegexValidator(regex=regex, message=message))

        return validators

    def get_question_options(self):
        """
        Gets all extra options stored at the question
        :return:
        """
        # Read the options field as if it is a dictionary object
        return ast.literal_eval(self.question.options)

    def save(self, value, inquiry):
        """ Save the answer of the question
        As each field is it's unique question, the form would become convoluted in saving all results.
        For that reason the field has become responsible instead as that has all the information stored to do so already

        :param value: The answered value
        :param inquiry: The inquiry object
        :return:
        """
        if not self.is_empty_value(value):
            # If the value is an actual answer
            inquiry_question_answer_obj = InquiryQuestionAnswer.objects.get_or_create(question=self.question, inquiry=inquiry)[0]
            if inquiry_question_answer_obj.answer != value:  # Answer has changed
                # A check to make sure that the answer wasn't already processed
                # This shouldn't happen at any point, but could happen when the questions are altered while an
                # inquiry is being filled in.
                if inquiry_question_answer_obj.processed:
                    raise RuntimeError("Inquiry is already processed and can't be altered")

                inquiry_question_answer_obj.answer = value
                inquiry_question_answer_obj.processed_answer = self.get_answer_option(value)
                inquiry_question_answer_obj.save()

        else:
            inquiry_question_answer_obj_query = InquiryQuestionAnswer.objects.filter(question=self.question, inquiry=inquiry)
            if inquiry_question_answer_obj_query.exists():
                # Revert the scoring if that has been processed
                if inquiry_question_answer_obj_query[0].processed:
                    inquiry_question_answer_obj_query[0].backward(inquiry)

                # Todo: remove next line
                InquiryQuestionAnswer.objects.filter(question=self.question, inquiry=inquiry).delete()

    def get_answer_option(self, value):
        """ Returns the answer option associated with the question type """
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
            inquiry_answer.forward()
        except ObjectDoesNotExist:
            # If the object does not exist yet, which can happen when no answer is given
            return

    def backward(self, inquiry):
        """
        Reverts the effects on the inquiry in a forwards motion
        :return:
        """
        try:
            inquiry_answer = InquiryQuestionAnswer.objects.get(inquiry=inquiry, question=self.question)
            inquiry_answer.backward()
        except ObjectDoesNotExist:
            # If the object does not exist yet, which is the case on empty answers
            return


class IgnorableQuestionFieldMixin(IgnorableFieldCheckMixin, QuestionFieldMixin):
    """ Combines two mixin for ease of use in remaining QuestionField classes """
    pass


class CharQuestionField(IgnorableQuestionFieldMixin, CharField):
    """ A CharField for a Char Question """
    widget = IgnorableInput

    def is_empty_value(self, value):
        return value is None or value == ""

    def get_answer_option(self, value):
        try:
            # Set the answer option to NotNone if it was answered
            if not self.is_empty_value(value):
                return AnswerOption.objects.get(question=self.question, answer="NotNone")
        except AnswerOption.DoesNotExist:
            # No option was made for this question
            return None


class IntegerQuestionField(IgnorableQuestionFieldMixin, IntegerField):
    """ An IntField for a Int Question """
    def get_answer_option(self, value):
        if value is None:
            return None

        options = AnswerOption.objects.filter(question=self.question)

        best_option = None
        best_value = -9999999
        # Go over all question options and select the answer that closest approximates the answer
        # Excludes all higher options
        for option in options:
            # Todo: change this to a database query, filter smaller than value, sort by value
            answer_value = int(option.answer)
            if best_value < answer_value <= value:
                best_value = answer_value
                best_option = option

        return best_option


class DecimalQuestionField(IgnorableQuestionFieldMixin, DecimalField):
    """ A decimal field for a decimal focussed question """
    def get_answer_option(self, value):
        if value is None:
            return None

        options = AnswerOption.objects.filter(question=self.question)

        best_option = None
        best_value = -9999999
        # Go over all question options and select the answer that closest approximates the answer
        # Excludes all higher options
        for option in options:
            # Todo: change this to a database query, filter smaller than value, sort by value
            answer_value = float(option.answer)
            if best_value < answer_value <= value:
                best_value = answer_value
                best_option = option

        return best_option


class ChoiceQuestionField(IgnorableQuestionFieldMixin, ChoiceField):
    """ A multiple choice question """
    widget = CustomRadioSelect

    def __init__(self, question, inquiry, *args, **kwargs):
        super(ChoiceQuestionField, self).__init__(question, inquiry, *args, **kwargs)

        choices = []
        images = {}

        # Get all the answer options and place them in a list
        for answer in question.answeroption_set.order_by("value"):
            choices.append((answer.value, answer.answer))
            # If answer option has an image, load that image onto the widget
            if answer.image:
                images[answer.value] = answer.image

        self.choices = choices
        self.widget.images = images

        question_options = self.get_question_options()
        # Set the height of the question
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


class InformationField(Field):
    """ A simple text based information field """
    widget = InformationDisplayWidget

    def __init__(self, page_entry_obj, *args, inquiry=None, **kwargs):
        super(InformationField, self).__init__(*args, **kwargs)
        self.name = "-- sample_name --"
        self.text = self.prep_text(page_entry_obj.text, inquiry=inquiry)
        self.label = ""
        self.required = False
        self.initial = self.text

    def save(self, *args, **kwargs):
        # There is nothing to save here, but the method can be called by Questionforms
        pass

    def forward(self, *args, **kwargs):
        # There is nothing to save here, but the method can be called by Questionforms
        pass

    def backward(self, *args, **kwargs):
        # There is nothing to save here, but the method can be called by Questionforms
        pass

    def prep_text(self, text, inquiry=None):
        """ Adjusts the text to better suit displaying it on screen """
        from Questionaire.processors.replace_text_from_database import format_from_database
        return format_from_database(text, inquiry=inquiry)


class IgnorableEmailField(IgnorableFieldCheckMixin, EmailField):
    widget = IgnorableEmailInput
