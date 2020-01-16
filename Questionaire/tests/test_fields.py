from django.core.exceptions import ValidationError
from django.test import TestCase

from Questionaire.models import *
from . import set_up_questionaire, set_up_inquiry, set_up_questionaire_scoring
from Questionaire.fields import IntegerQuestionField,\
    DecimalQuestionField, ChoiceQuestionField, CharQuestionField, IgnorableEmailField, QuestionFieldFactory


""" For language convenience we only test if it fails, not the exact error it gives
    If at some point that is wanted implement Django's assertFieldOutput method
"""


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
            raise AssertionError("{value} was not deemed valid: {error}".format(value=result, error=e.message))

    @staticmethod
    def assertNotValidates(field, value):
        """
        Asserts that a validation error is raised, no matter what context
        :param field: The field that is being cleaned
        :param value: The value (singular) that needs to be checked
        :return: An AssertionError if no ValidationError was raised, otherwise nothing
        """
        try:
            result = field.clean(value)
            raise AssertionError("{result} was incorrectly deemed valid".format(result=result))
        except ValidationError:
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
    def setUp(self):
        # Set up the database
        set_up_questionaire()
        set_up_questionaire_scoring()

    @staticmethod
    def get_ignorable_name(field):
        return field.name + field.widget.none_name_appendix

    def test_ignorable(self):
        fields = []
        inquiry = set_up_inquiry()

        # Integer question
        question = Question.objects.create(name="IntQ2", question_type=Question.TYPE_INT)
        fields.append(IntegerQuestionField(question, inquiry, required=False))

        # Double question
        question = Question.objects.create(name="DblQ2", question_type=Question.TYPE_DOUBLE)
        fields.append(DecimalQuestionField(question, inquiry, required=False))

        # Char question
        question = Question.objects.create(name="CharQ2", question_type=Question.TYPE_OPEN)
        fields.append(CharQuestionField(question, inquiry, required=False))

        # Choice question
        choice_question = Question.objects.get(name="ChoiceQ1")
        fields.append(IntegerQuestionField(question, inquiry, required=False))
        # A value that will result in a valid choice answer
        # this value is also used at the other question, but the answer is not relevant there
        res_value = choice_question.answeroption_set.first().value


        # EmailField
        fields.append(IgnorableEmailField(required=False))

        # In order test for,
        # 1) ignore_question used,
        # 2) ignore_question not used,
        # 3) required active, but ignore used (wost case, ideally this option is not displayed)
        # 4) a given answer is accepted on required=True

        for field in fields:
            self.assertValidates(field, field.widget.value_from_datadict(
                {'something_else': 'an_answer', self.get_ignorable_name(field): '1'},
                {}, field.name))
            self.assertNotValidates(field, field.widget.value_from_datadict(
                {"some_random_context": 'Maybe'}, {}, field.name))

            field.required = True
            self.assertNotValidates(field, field.widget.value_from_datadict(
                {'something_else': 'an_answer', self.get_ignorable_name(field): '1'},
                {}, field.name))
            self.assertValidates(field, field.widget.value_from_datadict(
                {'something_else': 'an_answer', field.name: '{value}'.format(value=res_value)},
                {}, field.name))

    def test_email_field(self):
        # There is an ignorable email field. Check that functionality is not broken due to it being ignorable
        # We just test that normal functionality still works and wasn't removed by ignorablefield
        field = IgnorableEmailField()
        self.assertValidates(field, ["a@a.be", "test_this@kotkt.nl", "w.s.roos@student.tue.nl"])
        self.assertNotValidates(field, "voornaam@achternaam")
        self.assertNotValidates(field, "@one.com")
        self.assertNotValidates(field, "one.com")


class FieldsTestCase(FieldTestMixin, TestCase):
    def setUp(self):
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



        # Todo: min/max validation implementation in question settings

    def test_double_field(self):
        question = Question.objects.create(name="DblQ3",question_type=Question.TYPE_DOUBLE)
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

        # Todo: min/max validation implementation in question settings
        # Todo: Maximum number of decimals implementation in question settings

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

        # Todo: Regex testing

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


class ExternalSourceTestCase(TestCase):
    # Todo: this
    pass