from django import template
from django.templatetags import static

from reports.models import ReportPage

register = template.Library()


@register.filter(takes_context=True)
def get_page_number(text, page):
    if "{page_number}" in text:
        page_number = ReportPage.objects.filter(report=page.report, page_number__lt=page.page_number).count()
        return text.replace("{page_number}", str(page_number))
    return text


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
