import math
from django.test import TestCase

from Questionaire.processors.code_translation import IdEncoder
from Questionaire.processors.replace_text_from_database import format_from_database
from Questionaire.models import Score, ScoringDeclaration, InquiryQuestionAnswer, Question, AnswerOption

from . import set_up_questionaire, set_up_questionaire_scoring, set_up_inquiry


class CodeTestCase(TestCase):
    """ This classes tests the encoding structure, i.e. the ability to retrieve id's from lettercodes """

    def test_code_reversal(self):
        """ Checks whether the forward and backward functionality return the same results """
        encoder = IdEncoder()

        # Ensure that the steps are a prime number
        upper_limit = math.floor(math.sqrt(encoder._steps))
        for i in range(2, upper_limit):
            if encoder._steps % i == 0:
                raise AssertionError("_steps is not a prime number")

        # Set a random collection of ids to be tested
        # We assume that only constant letters are used at least 6 times
        # (21^6=85,766,121 different combinations)
        ids = [1, 22, 176, 27842, 9643, 21270, 150001, 790248, 1000000, 45789123]
        for value in ids:
            """ Check a single id value if forward and backward functionality return the same results 
            If this isn't the case, there are likely to be multiple outcomes"""

            code = encoder.get_code_from_id(value)
            res_value = encoder.get_id_from_code(code)

            if res_value != value:
                raise AssertionError("{value} yielded {res_value}, but did not reverse to {code}".format(
                    value=value, res_value=res_value, code=code
                ))


class TextFormattingFromDbTestCase(TestCase):
    """ This class tests autoformatting of text with values from the database """

    def setUp(self):
        set_up_questionaire()
        set_up_questionaire_scoring()

    def test_value_retrieval(self):
        """ Tests retrieval of scoring values from the database """
        inquiry = set_up_inquiry()

        declaration = ScoringDeclaration.objects.get(name="tech_1_score")
        score = Score.objects.create(inquiry=inquiry, declaration=declaration)

        # Values are retrieved through the 'v_' marker
        message = "The value of tech_1_score is {v_tech_1_score}"

        # ##### Test with default value #####
        test_message = format_from_database(message, inquiry=inquiry)
        correct_message = message.format(v_tech_1_score=score.score)
        self.assertEqual(test_message, correct_message)

        # ##### Adjust the score to make sure it is not retrieving defaults #####
        score.score = 42
        score.save()
        score.refresh_from_db()  # Refresh to prevent Decimal artifacts from hanging around (42 != 42.00)

        test_message = format_from_database(message, inquiry=inquiry)
        correct_message = message.format(v_tech_1_score=score.score)
        self.assertEqual(test_message, correct_message)

        # ##### Test default value if score does not exist #####
        score.delete()

        test_message = format_from_database(message, inquiry=inquiry)
        correct_message = message.format(v_tech_1_score="")
        self.assertEqual(test_message, correct_message)

    def test_answer_retrieval(self):
        """ Tests answer retrieval from the database in given text """
        inquiry = set_up_inquiry()

        question = Question.objects.get(name="OpenQ1")
        # Values are retrieved through the 'q_' marker
        message = "The value of tech_1_score is {q_OpenQ1}"

        test_message = format_from_database(message, inquiry=inquiry)
        correct_message = message.format(q_OpenQ1="")
        self.assertEqual(test_message, correct_message)

        # Set an answer
        iqa = InquiryQuestionAnswer.objects.create(question=question, inquiry=inquiry, answer="An_answer")
        test_message = format_from_database(message, inquiry=inquiry)
        correct_message = message.format(q_OpenQ1=iqa.get_readable_answer())
        self.assertEqual(test_message, correct_message)

        # Change the answer
        iqa.answer = "Something else"
        iqa.save()
        iqa.refresh_from_db()

        test_message = format_from_database(message, inquiry=inquiry)
        correct_message = message.format(q_OpenQ1=iqa.get_readable_answer())
        self.assertEqual(test_message, correct_message)

    def test_choice_answer_retrieval(self):
        """ Tests that multiple choice questions return the selected answer and not the stored answer
        I.e. it does not return the reference to the answer option, but the answer option itself """
        inquiry = set_up_inquiry()

        question = Question.objects.get(name="ChoiceQ1")
        # Values are retrieved through the 'q_*__code' marker
        message = "The answer of tech_1_score is {q_ChoiceQ1}"

        # There is no answer yet
        test_message = format_from_database(message, inquiry=inquiry)
        correct_message = message.format(q_ChoiceQ1="")
        self.assertEqual(test_message, correct_message)

        answer = question.answeroption_set.first()
        question.answer_for_inquiry(inquiry=inquiry, answer_value=answer.value, process=True)

        # Check that the returned solution contains the selected answer and not the selected answer value
        test_message = format_from_database(message, inquiry=inquiry)
        correct_message = message.format(q_ChoiceQ1=answer.answer)
        self.assertEqual(test_message, correct_message)

    def test_code_retrieval(self):
        """ Tests that __code returns the code for the selected answer """
        inquiry = set_up_inquiry()

        question = Question.objects.get(name="ChoiceQ1")
        # Values are retrieved through the 'q_*__code' marker
        message = "The code of tech_1_score is {q_ChoiceQ1__code}"

        iqa = InquiryQuestionAnswer.objects.create(question=question, inquiry=inquiry, answer="An_answer")
        # Answer is not processed, so should return nothing
        test_message = format_from_database(message, inquiry=inquiry)
        correct_message = message.format(q_ChoiceQ1__code="")
        self.assertEqual(test_message, correct_message)

        # Set the code
        code_answer = "Answer number 1"
        option = question.answeroption_set.first()
        option.context_code = code_answer
        option.save()

        # set the answer option
        iqa.processed_answer = option
        iqa.save()

        # Answer is processed, so should return the answer
        test_message = format_from_database(message, inquiry=inquiry)
        correct_message = message.format(q_ChoiceQ1__code=code_answer)
        self.assertEqual(test_message, correct_message)
