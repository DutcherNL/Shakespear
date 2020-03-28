from django import template
from django.utils.html import escape

try:    # Try importing the breadcrumb module. This is not a required module so can be absent
    from django_bootstrap_breadcrumbs.templatetags.django_bootstrap_breadcrumbs import append_breadcrumb
except ImportError:
    append_breadcrumb = None

from PageDisplay import reverse_ns
from PageDisplay.models import BaseModule


register = template.Library()


@register.simple_tag(takes_context=True)
def breadcrumb(context, label, viewname, *args, **kwargs):
    """
    Expands breadcrumb with local namespace fucntionality.
    """
    if append_breadcrumb == None:
        return ''

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

    # Replace the widget according to the renderer. If widget == None it will default to the default widget
    widget = None
    # the page_tags function is occasionally used to render pages and module containers as well
    # so we need to assure it is a module before treating it as such
    if type(module) == BaseModule:
        # Get the name of the class type it actually is and not just a BaseModule
        module_class_name = type(module.get_child()).__name__
        if module_class_name in context['renderer'].replaced_widgets_dict.keys():
            widget = context['renderer'].replaced_widgets_dict[module_class_name]

    # Overlay should not be rendered, so just render the module itself
    return module.render(widget=widget, **flattened_context)


@register.simple_tag(takes_context=True)
def render_spacer(context, prev_module=None, container=None, field_name=None):
    """
    Renders the spacer (overlay for the empty spaces between modules)
    :param context: The current context (auto-inserted)
    :param container: the current module container
    :param field_name: the field_name on the module potentially edited
    :param prev_module: the rendered module just before this
    :return:
    """
    spacer = context.get('spacer', None)

    # No spacer was defined
    if spacer is None:
        return ''

    # Combine the context and any additional parameters together
    full_context = context.flatten()
    full_context.update({
        'container': container,
        'field_name': field_name,
        'prev_module': prev_module,
    })

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
