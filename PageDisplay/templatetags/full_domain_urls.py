from django import template

from general import get_absolute_url_path


register = template.Library()


@register.filter
def absolute_url(path):
    return get_absolute_url_path(path)