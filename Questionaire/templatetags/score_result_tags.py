from django import template
from Questionaire.models import Score, AnswerScoringNote, AnswerOption, InquiryQuestionAnswer

register = template.Library()

@register.filter
def get_tech_score(technology, inquiry):
    """
    Get the total technology score
    :param technology:
    :param inquiry:
    :return:
    """
    return technology.get_score(inquiry=inquiry)

@register.filter
def get_tech_scores(technology, inquiry):
    """
    Get all score objects for the given technology by a given user
    :param technology:
    :param inquiry:
    :return: A queryobject of filtered scores
    """
    return Score.objects.filter(
        inquiry=inquiry,
        declaration__in=technology.score_declarations.all())


@register.filter
def get_score_notes(score, technology):
    """

    :param technology: The technology
    :param score: The score object
    :return: A queryobject of notes
    """
    inq_question_answ = InquiryQuestionAnswer.objects.filter(inquiry=score.inquiry, processed=True)

    selected_answers = AnswerOption.objects.filter(inquiryquestionanswer__in=inq_question_answ)

    return AnswerScoringNote.objects.filter(technology=technology,
                                            scoring__declaration=score.declaration,
                                            scoring__answer_option__in=selected_answers)
