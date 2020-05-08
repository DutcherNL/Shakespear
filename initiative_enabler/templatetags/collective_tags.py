from django import template
from widget_tweaks.templatetags.widget_tweaks import FieldAttributeNode

from local_data_storage.models import DataColumn

register = template.Library()


@register.filter
def number_of_similar_inquiries(tech_collective, inquiry):
    """
    Returns the number of inquiries that are are also not matched
    """
    return tech_collective.get_similar_inquiries(inquiry).count()


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
        result += rsvp_agreed.inquirer.email + ';'
    return result