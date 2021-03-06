from django import template
from django.templatetags import static
from django.conf import settings
from django.utils.safestring import mark_safe

import os

from reports.utils import full_render_layout
from reports.models import ReportPage, PageLayout


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

@register.filter
def fix_url_string(url):
    """ A method that fixes an url string, on Windows there is a tendency for urls to be expressed with \\ instead of /.
    This method fixes that.
    :param url: The file url.
    :return: The fixed url string
    """""
    return str(url).replace("\\", "/")


class LocalStaticNode(static.StaticNode):
    def url(self, context):
        path = self.path.resolve(context)
        path = os.path.join(os.path.join(settings.BASE_DIR, 'assets/static/'), path).replace('\\', '/')
        print(path)
        return path


@register.tag('static')
def do_static(parser, token):
    """ Overrides the standard static to include the local adresses """
    return LocalStaticNode.handle_token(parser, token)


@register.simple_tag(takes_context=True)
def render_layout(context, layout=None, **kwargs):
    if layout is None:
        try:
            layout = context['report_page'].layout
        except KeyError:
            pass
    if layout:
        return full_render_layout(layout.template_content, context.get('layout_context', {}), **kwargs)
    return ''

