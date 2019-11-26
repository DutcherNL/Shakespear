from django import template


register = template.Library()

@register.simple_tag(takes_context=True)
def render_module(context, module, use_overlay=True):
    overlay = context.get('overlay', None)

    flattened_context = context.flatten()

    if module is not None:
        flattened_context['module'] = module


    # Whether to use the overlay on the modules
    if overlay and use_overlay:
        if overlay.use_overlay(**flattened_context):
            return overlay.render(**flattened_context)

    return module.render(**flattened_context)

