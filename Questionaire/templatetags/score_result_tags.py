from django import template
from django.db.models import Q, Count
from Questionaire.models import Score, AnswerScoringNote, AnswerOption, InquiryQuestionAnswer, TechScoreLink, Technology

register = template.Library()


@register.filter
def get_tech_score(technology, inquiry):
    """
    Get the total technology score
    :param technology:
    :param inquiry:
    :return:
    """
    if inquiry is None:
        # In case the inquiry is unknown
        return Technology.TECH_UNKNOWN

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
def get_as_score(score_link, inquiry):
    """
    Get all score objects for the given technology by a given user
    :param technology:
    :param inquiry:
    :return: A queryobject of filtered scores
    """
    return Score.objects.filter(
        inquiry=inquiry,
        declaration=score_link.score_declaration)[0]


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


@register.filter
def get_font_class_for_score(value):
    if value == 1:
        return "text-success"
    if value == 0:
        return "text-danger"
    return ""


@register.filter
def get_subtech_html_id(subtech, technology):
    return "st_" + str(technology.id) + "_" + str(subtech.id)


@register.filter
def create_sub_tech_accordion_name(technolgy):
    """ I wish this was not neccessary, but I can't get a good function with the add filter, it returns None :S """
    return "sub_accordion_{tech_id}".format(tech_id=technolgy.id)