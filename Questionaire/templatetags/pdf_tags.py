from django import template


register = template.Library()


@register.filter
def img(icon):
    return icon.path