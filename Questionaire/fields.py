from django.forms.fields import *
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError

from .widgets_question import *
from .widgets_question import IgnorableInputMixin
from .models import ExternalQuestionSource, InquiryQuestionAnswer, Question, AnswerOption
from .processors.question_processors import get_answer_option_through_question


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
            # Single choice question
            return ChoiceQuestionField(question, inquiry, required=required)
        if q_type == Question.TYPE_YESNO:
            # Yes / No question
            return YesNoQuestionField(question, inquiry, required=required)
        if q_type == Question.TYPE_BESTMULTI:
            # Multiple choice question
            return BestChoiceQuestionField(question, inquiry, required=required)

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
            current_answer = self.get_current_answer(inquiry)
            if current_answer:
                self.initial = current_answer
            else:
                # There is no answer, set the widget to empty (used for ignored widgets)
                self.widget.empty = True

        # Store the validators
        self.validators = [*self.validators, *self.construct_validators(self.question.options_dict)]

    def get_current_answer(self, inquiry):
        """ Returns the initial answer. Can be overwritten in case of multiple answers or complex answer retrieval """
        answer_obj = InquiryQuestionAnswer.objects.filter(question=self.question, inquiry=inquiry)
        if answer_obj.exists():
            return answer_obj.first().answer
        else:
            return None

    def construct_validators(self, validator_dict):
        """
        Constructs and returns the validators for the question
        :return: A list of validators
        """
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

    def get_answer_option(self, value):
        """ Returns the answer option associated with the question type """
        return get_answer_option_through_question(self.question, value)

    def is_empty_value(self, value):
        """
        Returns whether the given value is identified as an empty answer
        :param value: the given answer
        :return: whether the given entry is empty for this parameter
        """
        return value is None or value == 0 or value == ""


class IgnorableQuestionFieldMixin(IgnorableFieldCheckMixin, QuestionFieldMixin):
    """ Combines two mixin for ease of use in remaining QuestionField classes """
    pass


class CharQuestionField(IgnorableQuestionFieldMixin, CharField):
    """ A CharField for a Char Question """
    widget = IgnorableTextInput

    def is_empty_value(self, value):
        return value is None or value == ""


class ValueValidatorsOnQuestionMixin:
    def construct_validators(self, validator_dict):
        """
        Constructs and returns the validators for the question
        :return: A list of validators
        """
        validators = super().construct_validators(validator_dict)

        keys = validator_dict.keys()

        # There is a minimum validator
        if 'minimum' in keys:
            min_value = validator_dict.get('minimum')
            message = f'Value must be at least {min_value}'
            # Check if a custom regex message is present
            if 'minimum_message' in keys:
                message = validator_dict.get('minimum_message')
            validators.append(MinValueValidator(limit_value=min_value, message=message))

        # There is a maximum validator
        if 'maximum' in keys:
            max_value = validator_dict.get('maximum')
            message = f'Value can not exceed {max_value}'
            # Check if a custom regex message is present
            if 'maximum_message' in keys:
                message = validator_dict.get('maximum_message')
            validators.append(MaxValueValidator(limit_value=max_value, message=message))

        return validators


class IntegerQuestionField(ValueValidatorsOnQuestionMixin, IgnorableQuestionFieldMixin, IntegerField):
    """ An IntField for a Int Question """
    widget = IgnorableNumberInput


class DecimalQuestionField(ValueValidatorsOnQuestionMixin, IgnorableQuestionFieldMixin, DecimalField):
    widget = IgnorableDoubleInput


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

        question_options = self.question.options_dict
        # Set the height of the question
        if 'height' in question_options.keys():
            self.widget.answer_height = question_options['height']


class YesNoQuestionField(IgnorableQuestionFieldMixin, ChoiceField):
    """ A multiple choice question """
    widget = CustomRadioSelect

    def __init__(self, question, inquiry, *args, **kwargs):
        super(YesNoQuestionField, self).__init__(question, inquiry, *args, **kwargs)

        choices = []

        # Get all the answer options and place them in a list
        choices.append(('True', 'Ja'))
        choices.append(('False', 'Nee'))

        self.choices = choices

        def get_answer_image(answer_str):
            try:
                answer = question.answeroption_set.get(answer=answer_str)
                return answer.image
            except AnswerOption.DoesNotExist:
                pass

        self.widget.images = {
            'True': get_answer_image("True"),
            'False': get_answer_image("False"),
        }

        question_options = self.question.options_dict
        # Set the height of the question
        if 'height' in question_options.keys():
            self.widget.answer_height = question_options['height']


class BestChoiceQuestionField(IgnorableQuestionFieldMixin, MultipleChoiceField):
    """ A multiple choice question """
    widget = CustomMultiSelect

    def __init__(self, question, inquiry, *args, **kwargs):
        super(BestChoiceQuestionField, self).__init__(question, inquiry, *args, **kwargs)

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

        question_options = self.question.options_dict
        # Set the height of the question
        if 'height' in question_options.keys():
            self.widget.answer_height = question_options['height']

    def get_current_answer(self, inquiry):
        """ Returns the initial answer. Can be overwritten in case of multiple answers or complex answer retrieval """
        answer_values = super(BestChoiceQuestionField, self).get_current_answer(inquiry)

        # There are multiple selected answers, translate the values from the database to a list of id_nrs
        if answer_values:
            # Answer is a string representation of a list, so translate it.
            a = answer_values.strip('][').replace('\'', '').replace('\"', '').replace(' ', '')
            return a.split(',')
        return None


class InformationField(Field):
    """ A simple text based information field """
    widget = InformationDisplayWidget

    def __init__(self, page_entry_obj, *args, inquiry=None, **kwargs):
        super(InformationField, self).__init__(*args, **kwargs)
        self.name = f'info_{str(page_entry_obj.id)}'
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
