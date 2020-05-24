from django import template

from initiative_enabler.models import CollectiveRSVP, InitiatedCollective, TechCollectiveInterest
from initiative_enabler.forms import AdjustTechCollectiveForm

register = template.Library()


@register.filter
def number_of_interested_inquirers(tech_collective, inquirer):
    """
    Returns the number of inquiries that are are also not matched
    """
    return tech_collective.get_interested_inquirers(inquirer).count()


@register.filter
def phone2international(phone_number):
    """ Converts a phone number to an international number (assumes Dutch origin)"""
    phone_number = phone_number.strip()
    if phone_number.startswith("0"):
        phone_number = "+31"+phone_number[1:]
    return phone_number


@register.filter
def get_mail_list(collective):
    """ Returns the mail list of all agreed users for the clipboard """
    result = ""
    for rsvp_agreed in collective.collectiveapprovalresponse_set.all():
        result += rsvp_agreed.inquirer.email + '; '
    return result


@register.filter
def get_open_invitations(inquirer, technology):
    return CollectiveRSVP.objects.filter(
        inquirer=inquirer,
        collective__tech_collective__technology=technology,
        activated=False)


@register.filter
def get_joined_collectives(inquirer, technology):
    return InitiatedCollective.objects.filter(
        collectiveapprovalresponse__inquirer=inquirer,
        tech_collective__technology=technology
    )


@register.filter
def get_owned_collectives(inquirer, technology):
    return InitiatedCollective.objects.filter(
        inquirer=inquirer,
        tech_collective__technology=technology
    )


@register.filter
def get_current_tech_interest(inquirer, tech_collective):
    try:
        return TechCollectiveInterest.objects.get(inquirer=inquirer, tech_collective=tech_collective).is_interested
    except TechCollectiveInterest.DoesNotExist:
        return False


@register.filter
def invert(boolean):
    return not boolean


@register.simple_tag(takes_context=True)
def adjust_interest_form(context, tech_collective, new_state=None):
    inquirer = context['inquirer']
    if new_state is not None:
        initial = {
            'is_interested': new_state
        }
    else:
        initial = None

    return AdjustTechCollectiveForm(
        inquirer=inquirer,
        tech_collective=tech_collective,
        initial=initial,
    )