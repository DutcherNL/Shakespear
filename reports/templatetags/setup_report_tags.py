from django import template

from reports.forms import MovePageForm



register = template.Library()


@register.simple_tag()
def create_move_up_form(report_page):
    form = MovePageForm(
        report=report_page.reportpagelink.report,
        initial={
            'move_up': True,
            'report_page': report_page,
        }
    )
    return form.as_p()


@register.simple_tag()
def create_move_down_form(report_page):
    form = MovePageForm(
        report=report_page.reportpagelink.report,
        initial={
            'move_up': False,
            'report_page': report_page,
        }
    )
    return form.as_p()