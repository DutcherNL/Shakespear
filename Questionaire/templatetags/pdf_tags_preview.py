from django import template
from django.templatetags import static

register = template.Library()


@register.filter
def img(icon):
    return icon.url


@register.tag('static')
def do_static(parser, token):
    """
    A shell for the static module.
    In this context it works normally as it should, however is replaced in the pdf_tags
    """
    return static.StaticNode.handle_token(parser, token)
