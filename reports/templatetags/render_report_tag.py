from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag(takes_context=True)
def render_report(context, report):
    context_dict = context.flatten()

    page_num = 1
    rendered_html = ''

    for page in report.get_pages():
        rendered_html += page.render(**context_dict, report_page=page, p_num=page_num)
        page_num += 1

    return mark_safe(rendered_html)