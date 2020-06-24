from django import template
from Questionaire.models import Score, AnswerScoringNote, Technology, Inquirer

register = template.Library()


@register.filter
def get_logged_in_inquirer_code(request):
    try:
        inquirer_id = request.session.get('inquirer_id', None)
        if inquirer_id:
            inquirer = Inquirer.objects.get(id=inquirer_id)
            return inquirer.get_inquiry_code()
    except Inquirer.DoesNotExist:
        return ''


@register.filter
def get_current_inquirer_id(request):
    return request.session.get('inquirer_id', None)


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

    # Get the technology as a tech group as that means the score needs to be computed differently
    technology_as_tech_group = technology.get_as_techgroup
    if technology_as_tech_group:
        technology = technology_as_tech_group

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

    return AnswerScoringNote.get_all_notes(technology=technology, inquiry=score.inquiry)


@register.filter
def get_prepped_text(note, inquiry):
    return note.get_prepped_text(inquiry=inquiry)


@register.filter
def get_text_base_score(value):
    if value == 1:
        return "Aanbevolen"
    if value == 0:
        return "Niet aanbevolen"
    if value == 2:
        return "Wisselend"
    return "Geen advies"


@register.filter
def get_font_class_for_score(value):
    if value == 1:
        return "text-success"
    if value == 2:
        return "text-warning"
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
