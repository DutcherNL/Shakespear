from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def render_module(context, module, use_overlay=True):
    """ Render a module on the page """
    overlay = context.get('overlay', None)

    # Flatten the context to a single dictionary to be used in module render functions
    flattened_context = context.flatten()

    if module is not None:
        flattened_context['module'] = module

    # Whether to use the overlay on the modules
    if overlay and use_overlay:
        # Check if overlay allows itself to be used
        if overlay.use_overlay(**flattened_context):
            return overlay.render(**flattened_context)

    # Overlay should not be rendered, so just render the module itself
    return module.render(**flattened_context)

