from django.utils.safestring import mark_safe
from django.template.loader import get_template

from .models import BaseModule


def create_limited_copy(dictionary, *args):
    """ Creates a limited copy of the given dictionary containing the given arguments """
    new_dict = {}
    for arg in args:
        new_dict[arg] = dictionary.get(arg, None)
    return new_dict


class BaseWidgetOverlay:
    """  Overlay for module functionality """

    def render(self, request=None, using=None, module=None, **kwargs):
        if not self.use_overlay(module=module, **kwargs):
            return module.render(request=request, using=using, **kwargs)

        # Render the module
        context = self.get_context(module=module, **kwargs)
        template = get_template(self.template_name, using=using)
        rendered_result = template.render(context, request)

        # Return the result as safe
        return mark_safe(rendered_result)

    def get_context(self, module=None, **kwargs):
        context = create_limited_copy(kwargs, 'page_id', 'overlay', 'current_container', 'active_container')
        context['module'] = module
        return context

    def use_overlay(self, **kwargs):
        return True


class ModuleSelectOverlay(BaseWidgetOverlay):
    template_name = "pagedisplay/module_overlays/mo_selection.html"

    def use_overlay(self, active_container=None, current_container=None, **kwargs):
        try:
            ac_id = active_container.id
            cc_id = current_container.id
            if ac_id == cc_id:
                return True
        except AttributeError:
            # Either of the containers was None, so they aren't equeal anyway
            pass

        return False


class ModuleEditOverlay(BaseWidgetOverlay):
    template_name = "pagedisplay/module_overlays/mo_selected.html"

    def use_overlay(self, module=None, selected_module=None, **kwargs):
        # If the current module is the selected module
        if not isinstance(module, BaseModule):
            return False

        try:
            ac_id = module.id
            cc_id = selected_module.id
            if ac_id == cc_id:
                return True
        except AttributeError:
            # Either of the containers was None, so they aren't equeal anyway
            pass
        return False

    def get_context(self, module=None, **kwargs):
        context = super(ModuleEditOverlay, self).get_context(module, **kwargs)
        context['selected_module'] = kwargs.get('selected_module', None)
        return context
