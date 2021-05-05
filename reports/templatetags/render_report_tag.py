from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag(takes_context=True)
def render_report(context, report):
    context_dict = context.flatten()
    inquiry = context_dict.get('inquiry', None)

    page_num = 1
    rendered_html = ''

    for page in report.get_pages():
        meets_criteria = True
        for criteria in page.pagecriteria_set.all():
            if not criteria.is_met(inquiry):
                meets_criteria = False
        if meets_criteria:
            rendered_html += page.render(**context_dict, report_page=page, p_num=page_num)
            page_num += page.get_as_child().get_num_plotted_pages(inquiry)

    return mark_safe(rendered_html)
