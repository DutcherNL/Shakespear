import time
from django.test import TestCase

from Questionaire.models import *
from . import set_up_questionaire, set_up_inquiry, set_up_questionaire_scoring
from Questionaire.forms import QuestionPageForm


""" For Forms, we should only test that it can do what it should in the general context of the form
    e.g. the forward function should forward, but all edge cases for forward are tested in the test_model,
    we should only know that there is some link
"""


class QuestionFormTestCase(TestCase):
    def setUp(self):
        # Set up the database
        set_up_questionaire()
        set_up_questionaire_scoring()

    @staticmethod
    def set_up_form(page=None, data=None, inquiry=None):
        if page is None:
            page = Page.objects.order_by('position')[1]
        if inquiry is None:
            inquiry = set_up_inquiry()

        # Set default data
        data = data or {
            'IntQ1': 402,  # Selects the answer that adjust the Arb score (used in a later test case)
            'ChoiceQ1': AnswerOption.objects.get(value=21, answer="A").value
        }
        # Confirm that the page is valid
        form = QuestionPageForm(data=data, page=page, inquiry=inquiry)
        return form, inquiry, data

    def test_form_does_not_alter_other_questions(self):
        form, inquiry, data = self.set_up_form(page=Page.objects.order_by('position')[0])
        form.save(inquiry, save_raw=False)

        for answer in InquiryQuestionAnswer.objects.filter(inquiry=inquiry):
            # Loop over any found answers and confirm that they are empty
            # (it could also yield no answer objects which indicates the same)
            if not (answer.answer == '' or answer.answer is None):
                raise AssertionError("{0} unexpectantly contains an answer".format(answer))

    def test_form_alters_correct_questions(self):
        form, inquiry, data = self.set_up_form()
        form.save(inquiry, save_raw=False)

        for key, value in data.items():
            iqa = InquiryQuestionAnswer.objects.get(inquiry=inquiry, question__name=key)
            self.assertEqual(iqa.answer, str(value))
            self.assertIsNotNone(iqa.processed_answer)

    def test_form_can_save_raw_data(self):
        data = {
            'IntQ1': "AB",
            'ChoiceQ1': 525
        }
        form, inquiry, data = self.set_up_form(data=data)
        self.assertFalse(form.is_valid())
        form.save(inquiry, save_raw=False)
        # Answers should not have been saved normally, the form was not valid
        answers = InquiryQuestionAnswer.objects.filter(inquiry=inquiry)
        for answer in answers:
            # Loop over any found answers and confirm that they are empty
            # (it could also yield no answer objects which indicates the same)
            if not (answer.answer == '' or answer.answer is None):
                raise AssertionError("{0} unexpectantly contains an answer".format(answer))

        form.save(inquiry, save_raw=True)
        # Form should be saved with the raw, incorrect data

        for key, value in data.items():
            iqa = InquiryQuestionAnswer.objects.get(inquiry=inquiry, question__name=key)
            self.assertEqual(iqa.answer, str(value))
            self.assertIsNone(iqa.processed_answer)

    def test_forward_backward_processing(self):
        """ Tests a singular forward and backward processing, under the assumption it calls the methods
        tested in the models """
        form, inquiry, data = self.set_up_form()

        arb_declaration = ScoringDeclaration.objects.get(name="Arb_score")
        arb_score = Score.objects.get_or_create(declaration=arb_declaration, inquiry=inquiry)[0]
        form.save(inquiry, save_raw=False)

        self.assertEqual(arb_score.score, 0.5)
        # Forward the process
        form.forward(inquiry)
        arb_score.refresh_from_db()
        self.assertEqual(arb_score.score, 3.5)
        # Backward the process
        form.backward(inquiry)
        arb_score.refresh_from_db()
        self.assertEqual(arb_score.score, 0.5)
        # It is assumed that if this works, and the model base works, that the link works correctly

    def test_form_ignore_saving(self):
        """ Tests whether an ignored question is indeed ignored"""
        data = {
            'IntQ1_ignore': 1,
            'ChoiceQ1': 'ChoiceQ1_ignore'
        }
        form, inquiry, data = self.set_up_form(data=data)
        self.assertTrue(form.is_valid())

        for answer in InquiryQuestionAnswer.objects.filter(inquiry=inquiry):
            # Loop over any found answers and confirm that they are empty
            # (it could also yield no answer objects which indicates the same)
            if not (answer.answer == '' or answer.answer is None):
                raise AssertionError("{0} unexpectantly contains an answer".format(answer))

    def test_last_changed_update(self):
        form, inquiry, data = self.set_up_form()
        time_sample = inquiry.last_visited
        time.sleep(0.05)  # Sleep for a short amount of time to ensure that the time has changed
        form.save(inquiry)
        inquiry.refresh_from_db()
        self.assertNotEqual(inquiry.last_visited.timestamp(), time_sample.timestamp())

    def assertLastVisitedChanged(self, inquiry):
        """ Asserts that the last visited in the query is saved """
        time_sample = inquiry.last_visited
        inquiry.refresh_from_db()
        self.assertNotEqual(inquiry.last_visited.timestamp(), time_sample.timestamp())