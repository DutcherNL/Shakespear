from django import template

from initiative_enabler.models import CollectiveRSVP, InitiatedCollective, TechCollectiveInterest
from initiative_enabler.forms import AdjustTechCollectiveInterestForm

register = template.Library()


@register.filter
def number_of_interested_inquirers(tech_collective, inquirer):
    """
    Returns the number of inquiries that are are also not matched
    """
    return tech_collective.get_interested_inquirers(inquirer).count()


@register.filter
def get_collective_scope(requirement, inquirer):
    scope = requirement.get_as_child().get_collective_scope(inquirer)

    result = ''
    add_seperation = False
    for entry in scope:
        if add_seperation:
            result += ', '
        else:
            add_seperation = True
        result += entry

    return result


@register.filter
def get_collective_restrictions_as_strings(initiated_collective):
    collective_restrictions = {}
    for restriction_link in initiated_collective.tech_collective.restrictionlink_set.all():
        restriction = restriction_link.restriction
        restriction_values = initiated_collective.restriction_scopes.filter(restriction=restriction)

        if len(restriction_values) == 0:
            # Loop back when there are no results for this restriction, precaution for rare situations
            continue

        values = [value.value for value in restriction_values.order_by('value')]

        # Look for consequtive values and present them in a range form (... t/m ...)
        try:
            conseq_length = 0
            stored_start = int(values[0])
            remove_at = []
            for i in range(len(values)):
                current_value = values[i]
                try:
                    current_value = int(current_value)
                except ValueError:
                    pass
                if stored_start + conseq_length == current_value:
                    if i == len(values) - 1:
                        if conseq_length > 2:
                            values[i - conseq_length] = f'{values[i-conseq_length]} t/m {values[i-1]}'
                            for t in range(conseq_length):
                                remove_at.insert(0, i-conseq_length+t+1)
                    else:
                        conseq_length += 1
                else:
                    if conseq_length > 2:
                        values[i - conseq_length] = f'{values[i-conseq_length]} t/m {values[i-1]}'
                        for t in range(conseq_length - 1):
                            remove_at.insert(0, i-conseq_length+t+1)
                    if isinstance(current_value, int):
                        stored_start = int(values[i])
                        conseq_length = 1
                    else:
                        stored_start = conseq_length = 0
        except ValueError:
            pass
        for i in remove_at:
            values.pop(i)

        # Create an ordered string
        display_string = ''
        add_seperation = False
        for value in values:
            if add_seperation:
                display_string += ', '
            else:
                add_seperation = True
            display_string += str(value)

        collective_restrictions[restriction.public_name] = display_string
    return collective_restrictions.items()


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

    return AdjustTechCollectiveInterestForm(
        inquirer=inquirer,
        tech_collective=tech_collective,
        initial=initial,
    )