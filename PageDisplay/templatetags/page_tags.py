from django import template
from django.utils.html import escape

from django_bootstrap_breadcrumbs.templatetags.django_bootstrap_breadcrumbs import append_breadcrumb

from PageDisplay import reverse_ns


register = template.Library()


@register.simple_tag(takes_context=True)
def breadcrumb(context, label, viewname, *args, **kwargs):
    """
    Expands breadcrumb with local namespace fucntionality.
    """

    # Insert the namespace into the viewname
    namespace = context.get('request').resolver_match.namespace
    if len(namespace) > 0:
        viewname = namespace + ":" + viewname

    # Update the kwargs with the default url_kwargs
    kwargs.update(context.get('url_kwargs', {}))

    append_breadcrumb(context, escape(label), viewname, args, kwargs)
    return ''


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


@register.simple_tag(takes_context=True)
def render_spacer(context, **kwargs):
    spacer = context.get('spacer', None)

    # No spacer was defined
    if spacer is None:
        return ''

    # Combine the context and any additional parameters together
    full_context = context.flatten()
    full_context.update(kwargs)

    if spacer.use(**full_context):
        return spacer.render(**full_context)
    return ''


@register.simple_tag(takes_context=True)
def ns_url(context, url, **kwargs):
    """ Returns the url with the appended current namespace
     Also uses the right arguments to create the default url reversing """
    # Update the kwargs with the default url_kwargs
    kwargs.update(context.get('url_kwargs', {}))
    return reverse_ns(context.get('request'), url, kwargs=kwargs)
