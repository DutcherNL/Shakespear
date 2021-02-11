from django import template
from django.template.defaultfilters import urlize
from django.utils.safestring import mark_safe
from django.templatetags.static import StaticNode

from general import get_absolute_url_path

register = template.Library()


@register.filter
def urlize_new_tab(string):
    """ Enhances the urlize function to open urls in a new tab """
    return mark_safe(urlize(string).replace(
        '<a',
        '<a target="_blank" '
    ))


class AbsStaticNode(StaticNode):
    """ A tweak on the static node that instead returns absolute urls"""
    def url(self, context):
        path = super(AbsStaticNode, self).url(context)
        return get_absolute_url_path(path)


@register.tag('static_abs')
def do_static_abs(parser, token):
    """
    Similar to static tags, except it returns an absolute path instead
    """
    return AbsStaticNode.handle_token(parser, token)
