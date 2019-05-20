from django import template
from Questionaire.models import Score, AnswerScoringNote, AnswerOption

register = template.Library()


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
    selected_answers = AnswerOption.objects.filter(inquiryquestionanswer__inquiry=score.inquiry)

    return AnswerScoringNote.objects.filter(technology=technology,
                                            scoring__declaration=score.declaration,
                                            scoring__answer_option__in=selected_answers)
