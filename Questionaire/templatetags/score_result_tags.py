from django import template
from django.db.models import Q, Count
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
    Get the notes for the given score in the given technology
    :param technology: The technology
    :param score: The score object
    :return: A queryobject of notes
    """
    inq_question_answ = InquiryQuestionAnswer.objects.filter(inquiry=score.inquiry, processed=True)

    selected_answers = AnswerOption.objects.filter(inquiryquestionanswer__in=inq_question_answ)

    answer_notes = AnswerScoringNote.objects.filter(technology=technology,
                                            scoring__declaration=score.declaration,
                                            scoring__answer_option__in=selected_answers).\
                                            exclude(exclude_on__in=selected_answers)

    # Get all items in the queryset with include_on restrictions
    incomplete_entries = []
    for answerNote in answer_notes.annotate(
            num_includes=Count('include_on')).filter(num_includes__gt=0):
        # Loop over all include items and check if it is in there
        for includer in answerNote.include_on.all():
            if includer not in selected_answers:
                incomplete_entries.append(answerNote.id)
                break

    answer_notes = answer_notes.exclude(id__in=incomplete_entries)

    return answer_notes


@register.filter
def get_prepped_text(note, inquiry):
    return note.get_prepped_text(inquiry=inquiry)


@register.filter
def get_text_base_score(value):
    if value == 1:
        return "recommanded"
    if value == 0:
        return "not recommanded"
    return "unknown"

