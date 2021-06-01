from datetime import timedelta
from urllib.parse import urlencode

from django import template
from django.utils import timezone

from initiative_enabler.models import InitiatedCollective, CollectiveRestriction

register = template.Library()


@register.filter
def filter_recent(interest_queryset, days):
    date_threshold = timezone.now() - timedelta(days=days)
    return interest_queryset.filter(last_updated__gte=date_threshold)


@register.filter
def get_restriction_values(collective, restriction):
    return collective.restriction_scopes.filter(restriction=restriction)


@register.simple_tag(takes_context=True)
def updated_querystring(context, *args):
    """
    Returns a url-ready querystring based on the querystring of the current url adress, but with updated values as defined.
    :param context: The Template Context
    :param args: A list of pairs of arguments that need to be overwritten. E.g. "Age" 20 as arguments overwrites the
    parameter age with value 20
    :return: A urlencoded querystring
    """
    replacing_items = dict(zip(args[::2], args[1:][::2]))

    get_dict = context['request'].GET.copy()
    get_dict.update(replacing_items)
    return urlencode(get_dict)

