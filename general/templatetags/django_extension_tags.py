from django import template
from django.template.defaultfilters import urlize
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def urlize_new_tab(string):
    """ Enhances the urlize function to open urls in a new tab """
    return mark_safe(urlize(string).replace(
        '<a',
        '<a target="_blank" '
    ))