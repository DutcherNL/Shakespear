from django import template
from django.utils.safestring import mark_safe

from general import get_absolute_url_path


register = template.Library()


@register.filter
def absolute_url(path):
    return get_absolute_url_path(path)


@register.filter
def urls_in_new_tab(string):
    """ Adds the target to a new tab for any link encountered (requires <a> tags """
    return mark_safe(string.replace(
        '<a',
        '<a target="_blank" '
    ))