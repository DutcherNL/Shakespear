from django import template


register = template.Library()

@register.simple_tag(takes_context=True)
def render_module(context, module, **kwargs):
    request = context.get('request')
    overlay = context.get('overlay', None)
    inf_id = context.get('inf_id', None)
    return module.render(request=request, overlay=overlay, inf_id=inf_id, **kwargs)

