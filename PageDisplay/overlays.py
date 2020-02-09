from django.utils.safestring import mark_safe
from django.template.loader import get_template

from PageDisplay import create_limited_copy
from PageDisplay.models import BaseModule, ModuleContainer


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
        context = create_limited_copy(kwargs,
                                      'page_id',
                                      'overlay',
                                      'spacer'
                                      'current_container',
                                      'active_container',
                                      'url_kwargs',
                                      'template_engine')
        context['module'] = module
        return context

    def use_overlay(self, **kwargs):
        """
        A method whether the overlay should be used in the current context
        :param kwargs: A collection of given arguments from the render method
        :return: A boolean on whether the overlay is valid in this context
        """
        return True


class ModuleOverlayMixin:
    pass


class SpaceOverlayMixin:
    """ A mixin for overlays on spaces where modules can be """
    pass


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

    def use_overlay(self, **kwargs):
        if self._check_in_container(kwargs.get('active_container'), kwargs.get('current_container')):
            return super(OverlayInContainerMixin, self).use_overlay()
        return False


class ModuleSelectOverlay(OverlayInContainerMixin, BaseWidgetOverlay):
    """ Allows modules to be selected """
    template_name = "pagedisplay/module_overlays/mo_selection.html"


class ModuleEditOverlay(BaseWidgetOverlay):
    """ Displays the currently selected module """
    template_name = "pagedisplay/module_overlays/mo_selected.html"

    def __init__(self, *args, **kwargs):
        super(ModuleEditOverlay, self).__init__(*args, **kwargs)

    def use_overlay(self, module=None, selected_module=None, **kwargs):
        if super(ModuleEditOverlay, self).use_overlay(module=module, selected_module=selected_module, **kwargs):
            # Make sure that the module instance is of the type BaseModule (catch in case of coding error)
            if not isinstance(module, BaseModule):
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

    def get_context(self, module=None, **kwargs):
        context = super(ModuleEditOverlay, self).get_context(module, **kwargs)
        context['selected_module'] = kwargs.get('selected_module', None)
        return context
