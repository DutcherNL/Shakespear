from django.test import RequestFactory

from initiative_enabler.models import *
from Questionaire.models import *

__all__ = ['set_up_tech_scores', 'set_up_rsvp', 'generate_inquiry_with_score', 'set_up_tech_collective',
           'generate_interest_in_tech_collective', 'set_up_restrictions',
           'test_method_call']


def test_method_call(object, method_name, run_code):
    """ Ensures that a method on an object is run when running a piece of code"""
    def raise_run_time_error():
        raise RuntimeError("Method called")
    setattr(object, method_name, raise_run_time_error)

    try:
        run_code()
    except RuntimeError:
        pass
    else:
        raise AssertionError(f"{object.__class__}.{method_name} method was not called during saving")

def set_up_tech_collective(testcase):
    testcase.t4c_1 = Technology.objects.create(name="Tech_with_col_1")
    testcase.c_1 = TechCollective.objects.create(technology=testcase.t4c_1, description="Tech_with_col_1")
    generate_interest_in_tech_collective(testcase.c_1)
    generate_interest_in_tech_collective(testcase.c_1)
    generate_interest_in_tech_collective(testcase.c_1, interested=False)

    testcase.t4c_2 = Technology.objects.create(name="Tech_with_col_2")
    testcase.c_2 = TechCollective.objects.create(technology=testcase.t4c_2, description="Tech_with_col_2")
    generate_interest_in_tech_collective(testcase.c_2)
    generate_interest_in_tech_collective(testcase.c_2, interested=False)


def set_up_restrictions(testcase):
    # Generate a question
    testcase.q_1 = Question.objects.create(name="Restriction_test_1", question_type=Question.TYPE_OPEN)
    testcase.q_2 = Question.objects.create(name="Restriction_test_2", question_type=Question.TYPE_OPEN)

    # Set the restrictions
    testcase.rest_1 = CollectiveQuestionRestriction.objects.create(
        question=testcase.q_1,
        regex=None,
    )
    testcase.c_1.restrictions.add(testcase.rest_1)
    testcase.c_2.restrictions.add(
        CollectiveQuestionRestriction.objects.create(
            question=testcase.q_2,
            regex=None,
        )
    )

    testcase.inquirer_1 = generate_inquiry_with_answer(testcase.q_1, '1234').inquirer
    testcase.inquirer_2 = generate_inquiry_with_answer(testcase.q_1, 'OneTwo').inquirer
    testcase.inquirer_answerless = Inquirer.objects.create()
    Inquiry.objects.create(inquirer=testcase.inquirer_answerless)


def set_up_tech_scores(testcase, inquiry=None):
    t1 = Technology.objects.create(name="Tech_1", display_in_step_3_list=True)
    sd1 = ScoringDeclaration.objects.create(name="tech_1_score")
    TechScoreLink.objects.create(score_declaration=sd1, technology=t1)

    t2 = Technology.objects.create(name="Tech_2")
    sd2 = ScoringDeclaration.objects.create(name="tech_2_score")
    TechScoreLink.objects.create(score_declaration=sd2, technology=t2)

    inquiry_all = generate_inquiry_with_score(sd1, 10, inquiry=inquiry)
    generate_inquiry_with_score(sd2, 10, inquiry=inquiry_all)

    inquiry = generate_inquiry_with_score(sd1, -10)
    generate_inquiry_with_score(sd2, -10, inquiry=inquiry)

    inquiry = generate_inquiry_with_score(sd1, 10)
    generate_inquiry_with_score(sd2, 10, inquiry=inquiry)

    generate_inquiry_with_score(sd1, 10)
    generate_inquiry_with_score(sd2, -10)

    # pos/neg
    # T1: 3/1
    # T2: 2/2

    testcase.t1 = t1
    testcase.t2 = t2
    testcase.inquiry = inquiry_all


def generate_inquiry_with_score(declaration, score, inquiry=None):
    if inquiry is None:
        inquirer = Inquirer.objects.create()
        inquiry = Inquiry.objects.create(inquirer=inquirer)
    Score.objects.create(inquiry=inquiry, declaration=declaration, score=score)

    return inquiry


def generate_inquiry_with_answer(question, answer, inquiry=None):
    if inquiry is None:
        inquirer = Inquirer.objects.create()
        inquiry = Inquiry.objects.create(inquirer=inquirer)
    InquiryQuestionAnswer.objects.create(inquiry=inquiry, question=question, answer=answer)

    return inquiry


def generate_interest_in_tech_collective(tech_collective, inquirer=None, interested=True):
    if inquirer is None:
        inquirer = Inquirer.objects.create()

    return TechCollectiveInterest.objects.create(
        tech_collective=tech_collective,
        inquirer=inquirer,
        is_interested=interested,
    )


def get_get_request():
    get_request = RequestFactory().get('/')
    if not hasattr(get_request, 'session'):
        get_request.session = {}  # Set a dict for the session in case session data is needed at any point
    return get_request


def set_up_rsvp(testcase):
    tech = Technology.objects.create(name="rsvp_tech")

    tech_col_1 = TechCollective.objects.create(technology=tech, description="rsvp_tech description")

    # Generate a new inquiry to test the rsvps with
    inquirer = Inquirer.objects.create()
    active_collective = InitiatedCollective.objects.create(
        tech_collective=tech_col_1,
        inquirer=inquirer,
        name="Mr Test",
        message="Hello, ignore this invitation",
        phone_number="06 12345678"
    )

    CollectiveRSVP.objects.create(
        inquirer=Inquirer.objects.create(),
        collective=active_collective
    )
    CollectiveRSVP.objects.create(
        inquirer=Inquirer.objects.create(),
        collective=active_collective
    )

    rsvp = CollectiveRSVP.objects.create(
        inquirer=Inquirer.objects.create(email="testmail@test.io"),
        collective=active_collective
    )

    testcase.collective = active_collective
    testcase.rsvp = rsvp
