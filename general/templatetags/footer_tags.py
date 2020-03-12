from django import template
from general.models import BasePageURL

register = template.Library()


@register.simple_tag()
def general_pages(is_part_of_footer=False):
    if is_part_of_footer:
        return BasePageURL.objects.filter(in_footer=True).order_by('footer_order')
    else:
        return BasePageURL.objects.all()