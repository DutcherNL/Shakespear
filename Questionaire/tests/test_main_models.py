from django.test import TestCase

from Questionaire.models import *


def set_up_questionaire():
    # Create example questions
    int_question = Question.objects.create(name="IntQ1",
                                           question_text="This is a simple Integer question",
                                           question_type=Question.TYPE_INT)
    AnswerOption.objects.create(question=int_question, answer=400, value=11)
    AnswerOption.objects.create(question=int_question, answer=0, value=12)
    AnswerOption.objects.create(question=int_question, answer=50, value=13)
    AnswerOption.objects.create(question=int_question, answer=10, value=14)
    AnswerOption.objects.create(question=int_question, answer=2000, value=15)
    AnswerOption.objects.create(question=int_question, answer=150, value=16)

    choice_question = Question.objects.create(name="IntQ1",
                                              question_text="This is a simple Integer question",
                                              question_type=Question.TYPE_CHOICE)
    AnswerOption.objects.create(question=choice_question, answer="A", value=21)
    AnswerOption.objects.create(question=choice_question, answer="B", value=22)
    AnswerOption.objects.create(question=choice_question, answer="C", value=26)
    AnswerOption.objects.create(question=choice_question, answer="None of the above", value=999)

    # Create the pages
    page_1 = Page.objects.create(name="First_page",
                                 position=1)
    page_3 = Page.objects.create(name="Third_page",  # Page is the third page in the order,
                                 position=5)  # actual position shouldn't matter
    page_2 = Page.objects.create(name="Second_page",
                                 position=3)
    page_last = Page.objects.create(name="Last_page",
                                    position=99)

    # Create the first page
    PageEntryText.objects.create(text="This is the first page", page=page_1, position=1)
    PageEntryText.objects.create(text="This is the seconc page", page=page_2, position=1)
    PageEntryText.objects.create(text="This is the third page", page=page_3, position=1)
    PageEntryText.objects.create(text="This is the last page", page=page_last, position=1)

    PageEntryQuestion.objects.create(question=int_question, page=page_2, position=4)
    PageEntryQuestion.objects.create(question=choice_question, page=page_2, position=9)

    # Set up inclusive and exclusive page
    page_inclusive = Page.objects.create(name="inclusive", position=10)
    page_inclusive.include_on.add(int_question)
    page_exclusive = Page.objects.create(name="exclusive", position=11)
    page_exclusive.exclude_on.add(choice_question)


def set_up_inquiry():
    # Set up the inquirer and inquiry
    inquiry = Inquiry.objects.create()
    inquirer = Inquirer.objects.create(active_inquiry=inquiry)

    # Set up the first page (currently not done automatically)
    inquiry.set_current_page(Page.objects.order_by('position').first())

    return inquiry


def set_up_questionaire_scoring():
    t1 = Technology.objects.create(name="Tech_1")
    t2 = Technology.objects.create(name="Tech_2")
    t3 = Technology.objects.create(name="Tech_3")

    sd1 = ScoringDeclaration.objects.create(name="tech_1_score")
    sd2 = ScoringDeclaration.objects.create(name="tech_2_score", score_start_value=4)
    sd3 = ScoringDeclaration.objects.create(name="Arb_score")

    TechScoreLink.objects.create(score_declaration=sd1, technology=t1)
    TechScoreLink.objects.create(score_declaration=sd2, technology=t2, score_threshold_approve=25, score_threshold_deny=5)
    TechScoreLink.objects.create(score_declaration=sd2, technology=t3)

    answer_option = AnswerOption.objects.get(value=11)
    AnswerScoring.objects.create(answer_option=answer_option, declaration=sd1, score_change_value=1)
    AnswerScoring.objects.create(answer_option=answer_option, declaration=sd2, score_change_value=2)
    AnswerScoring.objects.create(answer_option=answer_option, declaration=sd3, score_change_value=3)


class QuestionTestCase(TestCase):
    def setUp(self):
        # Set up the database
        set_up_questionaire()
        set_up_questionaire_scoring()

    def test_basic_questionaire_set_up(self):
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

    def test_page_validness(self):
        """ Checks page validity check """
        inquiry = set_up_inquiry()
        p_excl = Page.objects.get(name="exclusive")
        p_incl = Page.objects.get(name="inclusive")

        # Check if pages are valid for the given inquiry
        self.assertTrue(p_excl.is_valid_for_inquiry(inquiry))
        self.assertFalse(p_incl.is_valid_for_inquiry(inquiry))

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



