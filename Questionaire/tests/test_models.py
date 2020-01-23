from django.db.utils import IntegrityError
from django.test import TestCase

from Questionaire.models import *
from . import set_up_questionaire, set_up_inquiry, set_up_questionaire_scoring


class PageTestCase(TestCase):
    def setUp(self):
        # Set up the database
        set_up_questionaire()
        set_up_questionaire_scoring()

    def test_page_set_up(self):
        """ Checks basic set up adheres the correct automatic assumptions """

        # Assert that the _entry types are copied correctly
        question_entry = PageEntryQuestion.objects.first()
        self.assertEqual(question_entry.entry_type, question_entry._entry_type)
        text_entry = PageEntryText.objects.first()
        self.assertEqual(text_entry.entry_type, text_entry._entry_type)

        # Check page assumptions
        page = Page.objects.get(position=3)
        # auto_process should default to False
        self.assertEqual(page.auto_process, False)

        # Check if page position is unique
        Page.objects.create(name="A random name", position=7853)
        try:
            Page.objects.create(name="Another page name", position=7853)
            AssertionError("Page position is not UNIQUE")
        except IntegrityError:
            pass  # All is well

    def test_pag_question_requirement(self):
        """ Check page validity for inclusive and exclusive questions
        Pages can be set to be included or excluded depending on whether certain questions have been answered
        exclusive excludes the page when a question is answered (regardless of the answer)
        inclusive includes the page when a question has been answered (regardless of the answer)
        """
        # Set up inclusive and exclusive page
        question = Question.objects.create(name="Page_req_question",
                                           question_text="This is used to check page question requirement",
                                           question_type=Question.TYPE_OPEN)

        page_inclusive = Page.objects.create(name="inclusive", position=70)
        page_inclusive.include_on.add(question)
        page_exclusive = Page.objects.create(name="exclusive", position=71)
        page_exclusive.exclude_on.add(question)

        inquiry = set_up_inquiry()

        # Check if pages are valid for the given inquiry
        # Question has not yet been answered
        self.assertTrue(page_exclusive.is_valid_for_inquiry(inquiry))
        self.assertFalse(page_inclusive.is_valid_for_inquiry(inquiry))

        # Create a mock answer
        # Note: all answers are always stored, so in this context it is specifically processed
        answer = InquiryQuestionAnswer.objects.create(inquiry=inquiry, question=question, answer="There is an answer")

        # Situation should not have been changed
        self.assertTrue(page_exclusive.is_valid_for_inquiry(inquiry))
        self.assertFalse(page_inclusive.is_valid_for_inquiry(inquiry))

        # Process the answer
        answer.processed = True
        answer.save()
        self.assertFalse(page_exclusive.is_valid_for_inquiry(inquiry))
        self.assertTrue(page_inclusive.is_valid_for_inquiry(inquiry))

    def test_page_score_requirement(self):
        """ A page can have a page requirement for a certain score """
        inquiry = set_up_inquiry()
        score_declaration = ScoringDeclaration.objects.create(score_start_value=4)

        # Create the page and the related requirement
        page = Page.objects.create(name="score_req", position=253)
        page_req = PageRequirement.objects.create(page=page,
                                                  score_declaration=score_declaration,
                                                  threshold=2,
                                                  comparison=0)
        # Create the score object so it can be adjusted by us more easily
        # This should automatically be done with the validity check, but we won't check that here
        score_obj = Score.objects.create(inquiry=inquiry, declaration=score_declaration)

        # Create a small method for looping convenience
        def check_for_stats(score, results):
            """ A loop for checking all possible outcomes"""
            # Adjust the score
            score_obj.score = score
            score_obj.save()

            for i in range(0, 5):
                page_req.comparison = i
                page_req.save()
                self.assertEqual(page.is_valid_for_inquiry(inquiry), results[i])

        """
        Comparison values:
          0: Greater then
          1: Greater then or equal
          2: Equal
          3: Lower or equal
          4: Lower
        """
        # Threshold was set to 2
        check_for_stats(3, [True, True, False, False, False])
        check_for_stats(2, [False, True, True, True, False])
        check_for_stats(1, [False, False, False, True, True])


class QuestionProcessingTestCase(TestCase):
    def setUp(self):
        # Set up the database
        set_up_questionaire()
        set_up_questionaire_scoring()

    def test_int_option_retrieval(self):
        question = Question.objects.get(name="IntQ1")
        inquiry = set_up_inquiry()

        answer_obj = InquiryQuestionAnswer(question=question, inquiry=inquiry)

        # Check higher than
        answer_obj.answer = 180
        answer_obj.get_answer_option(update_on_obj=True)
        self.assertEqual(answer_obj.processed_answer.answer, '150')

        # Check equal to an option
        answer_obj.answer = 50
        answer_obj.get_answer_option(update_on_obj=True)
        self.assertEqual(answer_obj.processed_answer.answer, '50')

        # Check no update version
        answer_obj.answer = 49
        temp_answer = answer_obj.get_answer_option(update_on_obj=False)
        self.assertEqual(temp_answer.answer, '10')
        self.assertEqual(answer_obj.processed_answer.answer, '50')  # check if answer_obj did not update

        # Check if below lowest option (there is no option below -1, so it should return None
        answer_obj.answer = -1
        self.assertIsNone(answer_obj.get_answer_option())

    def test_double_option_retrieval(self):
        question = Question.objects.get(name="DoubleQ1")
        inquiry = set_up_inquiry()

        answer_obj = InquiryQuestionAnswer(question=question, inquiry=inquiry)

        # Check higher than
        answer_obj.answer = 0.49
        answer_obj.get_answer_option(update_on_obj=True)
        self.assertEqual(answer_obj.processed_answer.answer, '0.25')

        # Check equal to an option
        answer_obj.answer = 0.5
        answer_obj.get_answer_option(update_on_obj=True)
        self.assertEqual(answer_obj.processed_answer.answer, '0.5')

        # Check no update version
        answer_obj.answer = 0.78
        temp_answer = answer_obj.get_answer_option(update_on_obj=False)
        self.assertEqual(temp_answer.answer, '0.75')
        self.assertEqual(answer_obj.processed_answer.answer, '0.5')  # check if answer_obj did not update

        # Check if below lowest option (there is no option below -1, so it should return None
        answer_obj.answer = -1
        self.assertIsNone(answer_obj.get_answer_option())

    def test_open_option_retrieval(self):
        question = Question.objects.get(name="OpenQ1")
        inquiry = set_up_inquiry()

        answer_obj = InquiryQuestionAnswer(question=question, inquiry=inquiry)

        # Check if an answer is filled in
        answer_obj.answer = "Some random answer"
        answer_obj.get_answer_option(update_on_obj=True)
        self.assertEqual(answer_obj.processed_answer.answer, 'NotNone')
        # Check if answer was left empty
        answer_obj.answer = None
        answer_obj.get_answer_option(update_on_obj=True)
        self.assertIsNone(answer_obj.processed_answer)

    def test_choice_option_retrieval(self):
        question = Question.objects.get(name="ChoiceQ1")
        inquiry = set_up_inquiry()

        answer_obj = InquiryQuestionAnswer(question=question, inquiry=inquiry)

        # Check higher than
        answer_obj.answer = 21
        answer_obj.get_answer_option(update_on_obj=True)
        self.assertEqual(answer_obj.processed_answer.answer, "A")
        answer_obj.answer = 999
        temp_answer = answer_obj.get_answer_option(update_on_obj=False)
        self.assertEqual(answer_obj.processed_answer.answer, "A")
        self.assertEqual(temp_answer.answer, "None of the above")
        answer_obj.answer = None
        answer_obj.get_answer_option(update_on_obj=True)
        self.assertIsNone(answer_obj.processed_answer)

    def test_start_scores(self):
        """ Tests if the processing of forward and backward of an answer option has the expected results on the scores
        Also check Technology processing, but not TechGroup processing
        """

        inquiry = set_up_inquiry()

        tech_1 = Technology.objects.get(name="Tech_1")
        tech_2 = Technology.objects.get(name="Tech_2")
        tech_3 = Technology.objects.get(name="Tech_3")

        arb_declaration = ScoringDeclaration.objects.get(name="Arb_score")
        arb_score = Score.objects.create(declaration=arb_declaration, inquiry=inquiry)

        # Ensure the situations
        self.assertEqual(tech_1.get_score(inquiry), Technology.TECH_UNKNOWN)
        self.assertEqual(tech_2.get_score(inquiry), Technology.TECH_FAIL)
        self.assertEqual(tech_3.get_score(inquiry), Technology.TECH_SUCCESS)
        self.assertEqual(arb_score.score, 0.5)

        # Process an answer option
        answer_option = AnswerOption.objects.get(value=11)
        answer_option.forward_for_inquiry(inquiry)
        # Refresh data from database to reflect changes in value
        arb_score.refresh_from_db()

        # Reflect the new scores
        self.assertEqual(tech_1.get_score(inquiry), Technology.TECH_SUCCESS)
        self.assertEqual(tech_2.get_score(inquiry), Technology.TECH_UNKNOWN)
        self.assertEqual(tech_3.get_score(inquiry), Technology.TECH_SUCCESS)
        self.assertEqual(arb_score.score, 3.5)

        # Revert the answer
        answer_option.backward_for_inquiry(inquiry)
        # Refresh data from database to reflect changes in value
        arb_score.refresh_from_db()

        # Ensure the situations
        self.assertEqual(tech_1.get_score(inquiry), Technology.TECH_UNKNOWN)
        self.assertEqual(tech_2.get_score(inquiry), Technology.TECH_FAIL)
        self.assertEqual(tech_3.get_score(inquiry), Technology.TECH_SUCCESS)
        self.assertEqual(arb_score.score, 0.5)

    def test_answer_processing(self):
        """ Test whether the processed state is used correctly """
        inquiry = set_up_inquiry()

        # Set up the score to track
        arb_declaration = ScoringDeclaration.objects.get(name="Arb_score")
        arb_score = Score.objects.create(declaration=arb_declaration, inquiry=inquiry)
        self.assertEqual(arb_score.score, 0.5)

        # Create the answer
        answer_option = AnswerOption.objects.get(value=11)
        answer_obj = InquiryQuestionAnswer(question=answer_option.question,
                                           inquiry=inquiry,
                                           processed_answer=answer_option)

        # Forward the result
        # This should fail as it was already processed
        answer_obj.processed = True
        answer_obj.forward()
        arb_score.refresh_from_db()
        self.assertEqual(arb_score.score, 0.5)

        # A non-processed answer should also fail
        answer_obj.processed = False
        answer_obj.backward()
        arb_score.refresh_from_db()
        self.assertEqual(arb_score.score, 0.5)

        # Check that something changes (exact value is not important for this test, just that it should change)
        # Checks that the state has changed as well
        answer_obj.forward()
        arb_score.refresh_from_db()
        self.assertNotEqual(arb_score.score, 0.5)
        self.assertTrue(answer_obj.processed)

        # Revert the state and check if the state is reverted accordingly
        answer_obj.backward()
        arb_score.refresh_from_db()
        self.assertEqual(arb_score.score, 0.5)
        self.assertFalse(answer_obj.processed)

    def test_question_answering(self):
        question = Question.objects.get(name="IntQ1")
        inquiry = set_up_inquiry()

        # Set the answer and get the answer object
        iqa_returned = question.answer_for_inquiry(inquiry, 180, process=False)
        iqa_found = InquiryQuestionAnswer.objects.get(question=question, inquiry=inquiry)

        # Test if the returned object is the right object
        self.assertEqual(iqa_found.id, iqa_returned.id)
        # Test if the answer is correct
        self.assertEqual(iqa_returned.answer, 180)
        # Test the process feature (should search the answer option)
        self.assertIsNone(iqa_returned.processed_answer)

        # Test autoprocess
        iqa_returned = question.answer_for_inquiry(inquiry, 173, process=True)
        self.assertEqual(iqa_returned.answer, 173)
        self.assertIsNotNone(iqa_returned.processed_answer)


class TechScoreNoteTestCase(TestCase):

    def setUp(self):
        # Set up the database
        set_up_questionaire()
        set_up_questionaire_scoring()
        self.setUp_notes()

    def setUp_notes(self):
        self.technology_1 = Technology.objects.get(name="Tech_1")
        self.technology_2 = Technology.objects.get(name="Tech_2")

        self.answer_score = AnswerScoring.objects.first()
        self.answer_option = self.answer_score.answer_option

        AnswerScoringNote.objects.create(scoring=self.answer_score, technology=self.technology_1, text="Text A")
        AnswerScoringNote.objects.create(scoring=self.answer_score, technology=self.technology_1, text="Text 1.2b")

        # Inclusive single
        note = AnswerScoringNote.objects.create(scoring=self.answer_score,
                                                technology=self.technology_1,
                                                text="Inclusive text")
        note.include_on.add(AnswerOption.objects.get(value=21))

        # Inclusive plural
        note = AnswerScoringNote.objects.create(scoring=self.answer_score,
                                                technology=self.technology_1,
                                                text="Inclusive text")
        note.include_on.add(AnswerOption.objects.get(value=21))
        note.include_on.add(AnswerOption.objects.get(value=31))

        # Multiple exclude options
        note = AnswerScoringNote.objects.create(scoring=self.answer_score,
                                                technology=self.technology_1,
                                                text="Exclusive text")
        note.exclude_on.add(AnswerOption.objects.get(value=22))
        note.exclude_on.add(AnswerOption.objects.get(value=26))

        # A random answer scoring note on another question that is not answered
        other_scoring_note = AnswerScoring.objects.last()
        self.other_answer_option = other_scoring_note.answer_option
        AnswerScoringNote.objects.create(scoring=other_scoring_note, technology=self.technology_1, text="A")
        AnswerScoringNote.objects.create(scoring=other_scoring_note, technology=self.technology_2, text="B")

    def test_note_base(self):
        """ Tests that the basic functionality of a single note appearing is done correctly """
        inquiry = set_up_inquiry()
        # ######## Test base function #######
        # Assert that it starts with a single note
        self.assertEqual(0, len(AnswerScoringNote.get_all_notes(self.technology_1, inquiry)))

        iqa = InquiryQuestionAnswer.objects.create(inquiry=inquiry,
                                                   question=self.answer_option.question,
                                                   answer="x",
                                                   processed_answer=self.answer_option)
        # Assert that it doesn't use a processed answer when the question is not processed
        self.assertEqual(0, len(AnswerScoringNote.get_all_notes(self.technology_1, inquiry)))

        # Assert it does us processed answers when the question is processed
        iqa.processed = True
        iqa.save()
        # 2 base + 1 exclude + 0 include
        self.assertEqual(3, len(AnswerScoringNote.get_all_notes(self.technology_1, inquiry)))

    def test_note_exclude(self):
        """ Test the exclude function workings on the note.
        Any option under exclude removes the note if any of the option have been processed """
        inquiry = set_up_inquiry()
        InquiryQuestionAnswer.objects.create(inquiry=inquiry,
                                             question=self.answer_option.question,
                                             answer="x",
                                             processed_answer=self.answer_option,
                                             processed=True)

        # ######## Test exclude function #######
        iqa2 = InquiryQuestionAnswer.objects.create(inquiry=inquiry,
                                                    question=self.answer_option.question,
                                                    answer="x",
                                                    processed_answer=AnswerOption.objects.get(value=22))
        # Not processed, not excluded
        self.assertEqual(3, len(AnswerScoringNote.get_all_notes(self.technology_1, inquiry)))
        # Proccesss it so it is excluded
        iqa2.processed = True
        iqa2.save()
        # 2 base + 0 exclude + 0 include
        self.assertEqual(2, len(AnswerScoringNote.get_all_notes(self.technology_1, inquiry)))

    def test_note_include(self):
        """ Test the workings of include functionality on the Note
        Include disables a note from being applicable if and only if all options under include are
        also processed in the inquiry """
        inquiry = set_up_inquiry()
        InquiryQuestionAnswer.objects.create(inquiry=inquiry,
                                             question=self.answer_option.question,
                                             answer="x",
                                             processed_answer=self.answer_option,
                                             processed=True)

        # ######## Test include function #######
        iqa2 = InquiryQuestionAnswer.objects.create(inquiry=inquiry,
                                                    question=self.answer_option.question,
                                                    answer="x",
                                                    processed_answer=AnswerOption.objects.get(value=21))
        # 2 base + 1 exclude + 0 include
        self.assertEqual(3, len(AnswerScoringNote.get_all_notes(self.technology_1, inquiry)))
        # Set include as not processed
        iqa2.processed = True
        iqa2.save()
        # 2 base + 1 exclude + 1 include
        self.assertEqual(4, len(AnswerScoringNote.get_all_notes(self.technology_1, inquiry)))

        # ######### Test plural includes ##########
        answer_option_3 = AnswerOption.objects.get(value=31)
        InquiryQuestionAnswer.objects.create(inquiry=inquiry,
                                             question=answer_option_3.question,
                                             answer="x",
                                             processed_answer=answer_option_3,
                                             processed=True)
        # 2 base + 1 exclude + 2 include
        self.assertEqual(5, len(AnswerScoringNote.get_all_notes(self.technology_1, inquiry)))

    def test_multiple_answers(self):
        """ Tests whether multiple answers containing notes are counted correctly """
        inquiry = set_up_inquiry()
        InquiryQuestionAnswer.objects.create(inquiry=inquiry,
                                             question=self.answer_option.question,
                                             answer="x",
                                             processed_answer=self.answer_option,
                                             processed=True)
        InquiryQuestionAnswer.objects.create(inquiry=inquiry,
                                             question=self.other_answer_option.question,
                                             answer="x",
                                             processed_answer=self.other_answer_option,
                                             processed=True)
        # 2 base + 1 exclude + 0 include + 1 external
        self.assertEqual(4, len(AnswerScoringNote.get_all_notes(self.technology_1, inquiry)))

        # 1 external (different technology)
        self.assertEqual(1, len(AnswerScoringNote.get_all_notes(self.technology_2, inquiry)))
