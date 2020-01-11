from Questionaire.models import *


def set_up_questionaire():
    """ Sets up the database for a simple questionaire """
    # Create example questions
    int_question = Question.objects.create(name="IntQ1",
                                           question_text="This is a simple Integer question",
                                           question_type=Question.TYPE_INT)
    AnswerOption.objects.create(question=int_question, answer=400, value=11)
    AnswerOption.objects.create(question=int_question, answer=5, value=12)
    AnswerOption.objects.create(question=int_question, answer=50, value=13)
    AnswerOption.objects.create(question=int_question, answer=10, value=14)
    AnswerOption.objects.create(question=int_question, answer=2000, value=15)
    AnswerOption.objects.create(question=int_question, answer=150, value=16)

    choice_question = Question.objects.create(name="ChoiceQ1",
                                              question_text="This is a simple Integer question",
                                              question_type=Question.TYPE_CHOICE)
    AnswerOption.objects.create(question=choice_question, answer="A", value=21)
    AnswerOption.objects.create(question=choice_question, answer="B", value=22)
    AnswerOption.objects.create(question=choice_question, answer="C", value=26)
    AnswerOption.objects.create(question=choice_question, answer="None of the above", value=999)

    double_question = Question.objects.create(name="DoubleQ1",
                                              question_text="This is a simple Double question",
                                              question_type=Question.TYPE_DOUBLE)
    AnswerOption.objects.create(question=double_question, answer=0, value=31)
    AnswerOption.objects.create(question=double_question, answer=0.25, value=32)
    AnswerOption.objects.create(question=double_question, answer=0.5, value=33)
    AnswerOption.objects.create(question=double_question, answer=0.75, value=34)
    AnswerOption.objects.create(question=double_question, answer=1, value=35)

    open_question = Question.objects.create(name="OpenQ1",
                                              question_text="This is a simple open question",
                                              question_type=Question.TYPE_OPEN)
    AnswerOption.objects.create(question=open_question, answer="NotNone", value=41)

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
    """ Creates and resturns a new inquiry """
    # Set up the inquirer and inquiry
    inquiry = Inquiry.objects.create()
    inquirer = Inquirer.objects.create(active_inquiry=inquiry)

    # Set up the first page (currently not done automatically)
    inquiry.set_current_page(Page.objects.order_by('position').first())

    return inquiry


def set_up_questionaire_scoring():
    """ Sets up basic scoring declarations.
    Can only be run after set_up_questionaire() has run """
    # Set up technologies
    t1 = Technology.objects.create(name="Tech_1")
    t2 = Technology.objects.create(name="Tech_2")
    t3 = Technology.objects.create(name="Tech_3")

    # Set up 3 scoring systems, one unrelated to any technology
    sd1 = ScoringDeclaration.objects.create(name="tech_1_score")
    sd2 = ScoringDeclaration.objects.create(name="tech_2_score", score_start_value=4)
    sd3 = ScoringDeclaration.objects.create(name="Arb_score")

    # Set the links
    TechScoreLink.objects.create(score_declaration=sd1, technology=t1)
    TechScoreLink.objects.create(score_declaration=sd2, technology=t2, score_threshold_approve=25,
                                 score_threshold_deny=5)
    TechScoreLink.objects.create(score_declaration=sd2, technology=t3)

    # Set the scoring
    answer_option = AnswerOption.objects.get(value=11)
    AnswerScoring.objects.create(answer_option=answer_option, declaration=sd1, score_change_value=1)
    AnswerScoring.objects.create(answer_option=answer_option, declaration=sd2, score_change_value=2)
    AnswerScoring.objects.create(answer_option=answer_option, declaration=sd3, score_change_value=3)
