from initiative_enabler.models import *
from Questionaire.models import *

__all__ = ['set_up_questionaires', 'set_up_rsvp', 'generate_inquiry_with_score']

def set_up_questionaires(testcase):
    t1 = Technology.objects.create(name="Tech_1")
    sd1 = ScoringDeclaration.objects.create(name="tech_1_score")
    TechScoreLink.objects.create(score_declaration=sd1, technology=t1)

    t2 = Technology.objects.create(name="Tech_2")
    sd2 = ScoringDeclaration.objects.create(name="tech_2_score")
    TechScoreLink.objects.create(score_declaration=sd2, technology=t2)

    inquiry_all = generate_inquiry_with_score(sd1, 10)
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


def set_up_rsvp(testcase):
    tech = Technology.objects.create(name="Collective_tech")

    tech_col_1 = TechCollective.objects.create(technology=tech, description="Collective_tech description")

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
