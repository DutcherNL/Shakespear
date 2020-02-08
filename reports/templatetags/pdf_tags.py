from django import template
from django.templatetags import static
from django.conf import settings

import os

from reports.models import ReportPage


register = template.Library()


@register.filter
def get_page_number(text, page):
    if "{page_number}" in text:
        page_number = ReportPage.objects.filter(report=page.report, page_number__lt=page.page_number).count()
        return text.replace("{page_number}", str(page_number))
    return text


@register.filter
def img(icon):
    return icon.path.replace('\\', '/')


class LocalStaticNode(static.StaticNode):
    def url(self, context):
        path = self.path.resolve(context)
        path = os.path.join(os.path.join(settings.BASE_DIR, 'assets/static/'), path).replace('\\', '/')
        return path


@register.tag('static')
def do_static(parser, token):
    """ Overrides the standard static to include the local adresses """
    return LocalStaticNode.handle_token(parser, token)

