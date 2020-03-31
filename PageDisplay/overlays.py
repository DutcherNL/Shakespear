from django.utils.safestring import mark_safe
from django.template.loader import get_template

from PageDisplay import create_limited_copy
from PageDisplay.models import BasicModuleMixin, ModuleContainer

__all__ = ['ModuleSelectOverlay', 'ModuleEditOverlay', 'HideModuleOverlay']


class BaseOverlay:
    """  Overlay for module functionality """
    exclude_containers = True

    def render(self, context=None, module=None):
        # Render the module
        context['widget'] = self.get_context(module=module)
        template = get_template(self.template_name, using=context.get('using', None))
        rendered_result = template.render(context, request=context.get('request'))

        # Return the result as safe
        return mark_safe(rendered_result)

    def get_context(self, module=None):
        return {'module': module}

    def use_overlay(self, context=None, module=None):
        """
        A method whether the overlay should be used in the current context
        :param context: A collection of given arguments from the render method
        :return: A boolean on whether the overlay is valid in this context
        """
        print(context)
        if self.exclude_containers:
            try:
                print("---- Overlay test")
                if module:
                    # Get the root form
                    module = module.get_child()
                print(module)
                print(issubclass(type(module), BasicModuleMixin))
                if not issubclass(type(module), BasicModuleMixin):
                    return False
            except KeyError:
                # Widget does not exist, so it's the root module
                return False

        return True


class OverlayInContainerMixin:
    """ A mixin that limits the use of the overlay in the active container only"""

    @staticmethod
    def _check_in_container(active_container, current_container):
        """
        Checks whether the overlay is currently in the container
        :param active_container: The selected/processed container
        :param current_container: The current container
        :return: Boolean
        """
        try:
            ac_id = active_container.id
            cc_id = current_container.id
            if ac_id == cc_id:
                return True
        except AttributeError:
            # Either of the containers was None, so they aren't equeal anyway
            pass

        return False

    def use_overlay(self, context=None):
        if self._check_in_container(context.get('active_container'), context.get('current_container')):
            return super(OverlayInContainerMixin, self).use_overlay(context=context)
        return False


class ModuleSelectOverlay(BaseOverlay):
    """ Allows modules to be selected """
    template_name = "pagedisplay/module_overlays/mo_selection.html"
    exclude_container = True


class ModuleEditOverlay(BaseOverlay):
    """ Displays the currently selected module """
    template_name = "pagedisplay/module_overlays/mo_selected.html"

    def __init__(self, *args, selected_module=None, **kwargs):
        super(ModuleEditOverlay, self).__init__(*args, **kwargs)
        self.selected_module = selected_module

    def use_overlay(self, context=None, module=None):
        if super(ModuleEditOverlay, self).use_overlay(context=context, module=module):
            selected_module = context.get('selected_module', None)
            # Make sure that the module instance is of the type BaseModule (catch in case of coding error)
            if not isinstance(module, BasicModuleMixin):
                return False

            return True

            # If the current module is the selected module
            try:
                ac_id = module.id
                cc_id = selected_module.id
                if ac_id != cc_id:
                    return True
            except AttributeError:
                # Either of the modules was None, so they aren't equeal anyway
                pass
            return False
        return False

    def get_context(self, module=None, **kwargs):
        context = super(ModuleEditOverlay, self).get_context(module, **kwargs)
        context['selected_module'] = self.selected_module
        return context


class HideModuleOverlay(BaseOverlay):
    """ Renders an entire module non-existent (i.e. does not render a given module) """

    def __init__(self, selected_module):
        self.selected_module = selected_module

    def render(self, **kwargs):
        return ""

    def use_overlay(self, context=None, module=None, **kwargs):
        if module.id == self.selected_module.id:
            return True
        return False
