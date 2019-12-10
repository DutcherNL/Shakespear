from django.utils.safestring import mark_safe
from django.template.loader import get_template

from .models import BaseModule, ModuleContainer


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
        """
        A method whether the overaly should be used in the current context
        :param kwargs: A collection of given arguments from the render method
        :return: A boolean on whether the overlay is valid in this context
        """
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

    def use_overlay(self, **kwargs):
        if self._check_in_container(kwargs.get('active_container'), kwargs.get('current_container')):
            return super(OverlayInContainerMixin, self).use_overlay()


class ModuleSelectOverlay(OverlayInContainerMixin, BaseWidgetOverlay):
    """ Allows modules to be selected """
    template_name = "pagedisplay/module_overlays/mo_selection.html"


class ModuleAddOverlay(OverlayInContainerMixin, BaseWidgetOverlay):
    """ Displays the relative location of the new module """
    template_name = "pagedisplay/module_overlays/mo_add.html"

    def __init__(self, *args, active_container=None, **kwargs):
        # Create 'empty' attributes
        self.append_to_end = False
        self.position = -1
        # Store the active container (i.e. in which a module will be added)
        self.active_container = active_container

        super(ModuleAddOverlay, self).__init__(*args, **kwargs)

    def use_overlay(self, module=None, **kwargs):
        if super(ModuleAddOverlay, self).use_overlay(module=module, **kwargs):
            if module == self.get_neighbouring_module:
                return True

        return False

    @property
    def get_neighbouring_module(self):
        """ Get the module that is neighbouring it
        It assumes originally that the new module will be before another module
        If it is added to the end. It will be displayed after the last availlable module
        """
        self.append_to_end = False
        if self.position == -1:
            return None

        module = self.active_container.basemodule_set.filter(position__gte=self.position).order_by('position').first()
        if module is None:
            self.append_to_end = True
            return self.active_container.basemodule_set.order_by('position').last()
        return module

    def get_context(self, **kwargs):
        context = super(ModuleAddOverlay, self).get_context(**kwargs)
        context['append_to_end'] = self.append_to_end
        return context


class ModuleEditOverlay(OverlayInContainerMixin, BaseWidgetOverlay):
    """ Displays the currently selected module """
    template_name = "pagedisplay/module_overlays/mo_selected.html"

    def use_overlay(self, module=None, selected_module=None, **kwargs):
        if super(ModuleEditOverlay, self).use_overlay(module=module, selected_module=selected_module, **kwargs):
            # Make sure that the module instance is of the type BaseModule (catch in case of coding error)
            if not isinstance(module, BaseModule):
                return False

            # If the current module is the selected module
            try:
                ac_id = module.id
                cc_id = selected_module.id
                if ac_id == cc_id:
                    return True
            except AttributeError:
                # Either of the modules was None, so they aren't equeal anyway
                pass
            return False

    def get_context(self, module=None, **kwargs):
        context = super(ModuleEditOverlay, self).get_context(module, **kwargs)
        context['selected_module'] = kwargs.get('selected_module', None)
        return context
