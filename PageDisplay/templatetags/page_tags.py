from django import template


register = template.Library()

@register.simple_tag
def render_module(module, request, **kwargs):
    return module.render(request=request, **kwargs)

