from django.core.exceptions import ValidationError
from django.test import TestCase
from decimal import *

from Questionaire.models import *
from . import set_up_questionaire, set_up_inquiry, set_up_questionaire_scoring
from Questionaire.fields import IntegerQuestionField, \
    DecimalQuestionField, ChoiceQuestionField, CharQuestionField, IgnorableEmailField, QuestionFieldFactory
from Questionaire.widgets_question import ExternalDataInput, ExternalDataInputLocal

from local_data_storage.tests import DataContentTestMixin

""" For language convenience we only test if it fails, not the exact error it gives
    If at some point that is wanted implement Django's assertFieldOutput method
"""


def adjust_question_options(question, update=True, **kwargs):
    """ Adjusts the options of the question
    :param question: The question changed
    :param update: whether the current options need to be updated (False ignores any content present)
    """
    # If update, get the original options, otherwise start with an empty dict
    if update:
        options = question.options_dict
    else:
        options = {}

    # Update the options with the defined options
    options.update(kwargs)
    # save the options in a string based form
    question.options = str(kwargs)
    question.save()


class FieldTestMixin:
    @staticmethod
    def assertValidates(field, value):
        """
        Asserts that the value validates
        :param field: the field
        :param value: The value to be tested against. Can be a single value or a list of values
        :return: An AssertionError if a ValidationError was raised, otherwise nothing
        """
        try:
            if isinstance(value, list):
                for v in value:
                    result = v
                    field.clean(v)
            else:
                result = value
                field.clean(value)
        except ValidationError as e:
            raise AssertionError(f'"{result}" was not deemed valid')

    @staticmethod
    def assertNotValidates(field, value, message=None):
        """
        Asserts that a validation error is raised, no matter what context
        :param field: The field that is being cleaned
        :param value: The value (singular) that needs to be checked
        :param message: If a message is given, it will check if the given validation error matches this string
        :return: An AssertionError if no ValidationError was raised, otherwise nothing
        """
        try:
            result = field.clean(value)
            raise AssertionError("{result} was incorrectly deemed valid".format(result=result))
        except ValidationError as error:
            if message is not None:
                if error.messages[0] != message:
                    raise AssertionError(f'Wrong error message returned: "{error.messages}" instead of "{message}"')

            return


class FieldFactoryTestCase(FieldTestMixin, TestCase):
    def setUp(self):
        # Set up the database
        set_up_questionaire()
        set_up_questionaire_scoring()

    def test_field_factory(self):
        """ Test the field factory. The Field Factory constructs fields from the question"""
        inquiry = set_up_inquiry()

        question = Question.objects.create(name="IntQ4", question_type=Question.TYPE_INT)
        field = QuestionFieldFactory.get_field_by_questionmodel(question=question, inquiry=inquiry)
        self.assertTrue(isinstance(field, IntegerQuestionField))

        question = Question.objects.create(name="DoubleQ4", question_type=Question.TYPE_DOUBLE)
        field = QuestionFieldFactory.get_field_by_questionmodel(question=question, inquiry=inquiry)
        self.assertTrue(isinstance(field, DecimalQuestionField))

        question = Question.objects.create(name="ChoiceQ4", question_type=Question.TYPE_CHOICE)
        field = QuestionFieldFactory.get_field_by_questionmodel(question=question, inquiry=inquiry)
        self.assertTrue(isinstance(field, ChoiceQuestionField))

        question = Question.objects.create(name="CharQ4", question_type=Question.TYPE_OPEN)
        field = QuestionFieldFactory.get_field_by_questionmodel(question=question, inquiry=inquiry)
        self.assertTrue(isinstance(field, CharQuestionField))


class TestIgnorableTestCase(FieldTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up the database
        set_up_questionaire()
        set_up_questionaire_scoring()

    @staticmethod
    def get_ignorable_name(field, key):
        return key + field.widget.none_name_appendix

    def test_ignorable(self):
        fields = {}
        answers = {}
        inquiry = set_up_inquiry()

        # Integer question
        question = Question.objects.create(name="IntQ2", question_type=Question.TYPE_INT)
        fields['Q_1'] = IntegerQuestionField(question, inquiry, required=False)
        answers['Q_1'] = 4

        # Double question
        question = Question.objects.create(name="DblQ2", question_type=Question.TYPE_DOUBLE)
        fields['Q_2'] = DecimalQuestionField(question, inquiry, required=False)
        answers['Q_2'] = 4.0

        # Char question
        question = Question.objects.create(name="CharQ2", question_type=Question.TYPE_OPEN)
        fields['Q_3'] = CharQuestionField(question, inquiry, required=False)
        answers['Q_3'] = "answer"

        # Choice question
        choice_question = Question.objects.get(name="ChoiceQ1")
        fields['Q_4'] = IntegerQuestionField(question, inquiry, required=False)
        # A value that will result in a valid choice answer
        # this value is also used at the other question, but the answer is not relevant there
        answers['Q_4'] = choice_question.answeroption_set.first().value

        # Email field
        fields['Q_5'] = IgnorableEmailField(required=False)
        answers['Q_5'] = "home@google.com"

        # In order test for,
        # 1) ignore_question used,
        # 2) ignore_question not used,
        # 3) required active, but ignore used (wost case, ideally this option is not displayed)
        # 4) a given answer is accepted on required=True

        for key, field in fields.items():
            self.assertValidates(field, field.widget.value_from_datadict(
                {'something_else': 'an_answer', self.get_ignorable_name(field, key): '1'},
                {}, key))
            self.assertNotValidates(field, field.widget.value_from_datadict(
                {"some_random_context": 'Maybe'}, {}, key))

            field.required = True
            self.assertNotValidates(field, field.widget.value_from_datadict(
                {'something_else': 'an_answer', self.get_ignorable_name(field, key): '1'},
                {}, key))
            self.assertValidates(field, field.widget.value_from_datadict(
                {'something_else': 'an_answer', key: '{value}'.format(value=answers[key])},
                {}, key))

    def test_email_field(self):
        # There is an ignorable email field. Check that functionality is not broken due to it being ignorable
        # We just test that normal functionality still works and wasn't removed by ignorablefield
        field = IgnorableEmailField()
        self.assertValidates(field, ["a@a.be", "test_this@kotkt.nl", "w.s.roos@student.tue.nl"])
        self.assertNotValidates(field, "voornaam@achternaam")
        self.assertNotValidates(field, "@one.com")
        self.assertNotValidates(field, "one.com")


class FieldsTestCase(FieldTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up the database
        set_up_questionaire()
        set_up_questionaire_scoring()

    def test_int_field(self):
        question = Question.objects.create(name="IntQ3", question_type=Question.TYPE_INT)
        inquiry = set_up_inquiry()
        answer = 3
        question.answer_for_inquiry(inquiry, answer, process=False)
        field = IntegerQuestionField(question, inquiry, required=False)

        # Test initial values
        self.assertEqual(field.initial, str(answer))

        # Test validation
        self.assertValidates(field, [-2, 0, 3])
        self.assertNotValidates(field, 3.1)
        self.assertNotValidates(field, "Uh")
        self.assertNotValidates(field, "4b")

        # Test validation options
        question.options = str({
            'minimum': 2,
            'minimum_message': "MIN_MESSAGE",
            'maximum': 7,
            'maximum_message': "MAX_MESSAGE"
        })
        question.save()

        field = IntegerQuestionField(question, inquiry, required=False)

        # Ensure that the miniumm and maximum values are upheld (min and max are inclusive for itself
        self.assertValidates(field, [2, 3, 7])
        self.assertNotValidates(field, 1, message="MIN_MESSAGE")
        self.assertNotValidates(field, 8, message="MAX_MESSAGE")

    def test_double_field(self):
        question = Question.objects.create(name="DblQ3", question_type=Question.TYPE_DOUBLE)
        inquiry = set_up_inquiry()
        answer = 4.2
        question.answer_for_inquiry(inquiry, answer, process=False)
        field = DecimalQuestionField(question, inquiry, required=False)

        # Test initial values
        self.assertEqual(field.initial, str(answer))

        # Test validation
        self.assertValidates(field, [-2.1, 0, 3.1502, 4.9])
        self.assertNotValidates(field, "Uh")
        self.assertNotValidates(field, "4b")

        # Test validation options
        adjust_question_options(question,
                                minimum=2.3,
                                minimum_message="MIN_MESSAGE_2",
                                maximum=7.3,
                                maximum_message="MAX_MESSAGE_2")

        field = DecimalQuestionField(question, inquiry, required=False)

        # Ensure that the miniumm and maximum values are upheld (min and max are inclusive for itself
        self.assertValidates(field, [2.3, 3, 7.2, Decimal(7.3)])
        self.assertNotValidates(field, 2.1, message="MIN_MESSAGE_2")
        self.assertNotValidates(field, 7.4, message="MAX_MESSAGE_2")

    def test_char_field(self):
        question = Question.objects.create(name="OpenQ3", question_type=Question.TYPE_OPEN)
        inquiry = set_up_inquiry()
        answer = "the answer"
        question.answer_for_inquiry(inquiry, answer, process=False)
        field = CharQuestionField(question, inquiry, required=False)

        # Test initial values
        self.assertEqual(field.initial, str(answer))

        # Test validation
        self.assertValidates(field, ["-2.1", "Say", "Well hello"])

        # Test validation options
        adjust_question_options(question,
                                regex='^[0-9]{4}[A-Z]{2}$',
                                regex_message="REGEX_FAIL")

        field = CharQuestionField(question, inquiry, required=False)

        # Another approach would be to validate the presence of a RegexValidator with the given regex.
        # This was easier to implement imo XD

        self.assertValidates(field, ['1234AB', '9929ZU'])

        # These all should throw validation errors for non-matching regex patterns
        self.assertNotValidates(field, '1234', message="REGEX_FAIL")  # Test incomplete validity
        self.assertNotValidates(field, '567AI', message="REGEX_FAIL")  # Test incorrect number of elements
        self.assertNotValidates(field, '2589nm', message="REGEX_FAIL")  # Test incorrect imput elements
        self.assertNotValidates(field, 'not 8765AB', message="REGEX_FAIL")  # Test start marker workings
        self.assertNotValidates(field, '8765AB yay', message="REGEX_FAIL")  # Test end marker workings

    def test_choice_field(self):
        """ Tests the retrieval logic of the choice fields.
        Choice fields use the value parameter to communicate the selected option
        """
        inquiry = set_up_inquiry()
        question = Question.objects.get(name="ChoiceQ1")
        answer = question.answeroption_set.first().value
        question.answer_for_inquiry(inquiry, answer, process=False)

        field = ChoiceQuestionField(question=question, inquiry=inquiry, required=False)

        # Test initial value
        self.assertEqual(field.initial, str(answer))

        # Test that all valid options are valid
        options = question.answeroption_set.order_by('value')
        for option in options:
            self.assertValidates(field, option.value)

        # Test that an option with the same value can not cause a conflict (i.e. a get uses only the value argument)
        q2 = Question.objects.create(question_type=Question.TYPE_CHOICE)
        AnswerOption.objects.create(question=q2, value=options.last().value)
        self.assertValidates(field, options.last().value)

        # Test that some of the invalid options are not valid
        # Filter for all options that are not equal to the values in the valid options
        values = options.values('value')
        options = AnswerOption.objects.exclude(value__in=values)
        # Check the first and last option (can also insert any other option)
        self.assertNotValidates(field, options.first().value)
        self.assertNotValidates(field, options.last().value)


class ExternalSourceTestCase(FieldTestMixin, DataContentTestMixin, TestCase):
    """"
    Any field with a question that is 'linked' should have the external_source_widget implemented
    The widget needs to be tested
    """
    @classmethod
    def setUpTestData(cls):
        cls.questions = {}

        def make_linked_question(name, type, code_source, attribute=None):
            question = Question.objects.create(name=f'Ext_Q_{name}',
                                               question_type=type)
            if attribute is None:
                attribute = cls.dt_2_c_chr
            # Note, most calls to this method set code_source as a literal string instead of a reference
            # This prevents the need to create a whole new question with the entire answer structure
            ExternalQuestionSource.objects.create(question=question,
                                                  local_table=cls.dt_2,
                                                  local_attribute=attribute,
                                                  code_source=code_source)

            return question

        # Create base cases
        cls.questions['int'] = make_linked_question("int", Question.TYPE_INT, "1234AB", attribute=cls.dt_2_c_int)
        cls.questions['double'] = make_linked_question("double", Question.TYPE_DOUBLE, "1234AB", attribute=cls.dt_2_c_flt)
        cls.questions['char'] = make_linked_question("chr", Question.TYPE_OPEN, "1234AB", attribute=cls.dt_2_c_chr)
        cls.questions['choice'] = make_linked_question("choice", Question.TYPE_CHOICE, "1234AB", attribute=cls.dt_2_c_chr)

        cls.questions['q_omit'] = make_linked_question("q_omit", Question.TYPE_INT, "4040NF", attribute=cls.dt_2_c_flt)

        # Used for bouncing answers
        cls.questions['q_bounce'] = make_linked_question("q_bounce", Question.TYPE_INT, "5875KH")

        # Used for query testing
        cls.questions['source'] = Question.objects.create(name="source", question_type=Question.TYPE_OPEN)
        cls.questions['q_query'] = make_linked_question("q_query", Question.TYPE_INT, "{q_source}", attribute=cls.dt_2_c_flt)

        # Generate the data entries
        cls.DataFieldContent.objects.create(key='1234AB', int_field=10, flt_field=25, chr_field='hey')
        cls.DataFieldContent.objects.create(key='2363KH', flt_field=7.9)
        cls.DataFieldContent.objects.create(key='4040NF', int_field=4)

    def test_external_widget_presence(self):
        """ Checks that the widget in the fields have been set to the correct widget """

        inquiry = set_up_inquiry()
        for key, question in self.questions.items():
            # Check for the four basic question types that it uses an externalDataInput Widget
            if key in ['int', 'double', 'char', 'choice']:
                field = QuestionFieldFactory.get_field_by_questionmodel(question=question, inquiry=inquiry)
                # Test that the widget is correctly replaced
                if not isinstance(field.widget, ExternalDataInput):
                    raise AssertionError(f'Widget of {key} is not of type ExternalDataInput')

    def test_widget_retrieval(self):
        """ Tests that the widget uses retrieval from the database """
        inquiry = set_up_inquiry()
        # Test the value_from_datadict method. Nothing needs to be added as data will be retrieved from the server
        def assertCorrectRetrieval(q_name, value):
            widget = ExternalDataInputLocal(inquiry, self.questions[q_name].externalquestionsource)
            retrieved_value = widget.value_from_datadict(None, None, None)
            if retrieved_value != value:
                raise AssertionError(f'Widget did not retrieve the correct value. {retrieved_value} instead of {value}')

        assertCorrectRetrieval('int', 10)
        assertCorrectRetrieval('double', 25)
        assertCorrectRetrieval('char', 'hey')

        # Test that omitted attributes or missing key entries do not result results
        assertCorrectRetrieval('q_omit', None)
        assertCorrectRetrieval('q_bounce', None)

        # Test that the widget uses the format from database processor
        widget = ExternalDataInputLocal(inquiry, self.questions['q_query'].externalquestionsource)
        # No answer is available, so it should return None
        self.assertIsNone(widget.value_from_datadict(None, None, None))
        # Set an answer and test it (should return 7.9)
        iqa = InquiryQuestionAnswer.objects.create(question=self.questions['source'], inquiry=inquiry, answer="2363KH")
        assertCorrectRetrieval('q_query', 7.9)
        pass



