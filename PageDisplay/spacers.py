from django.utils.safestring import mark_safe
from django.template.loader import get_template

import math

from .models import VerticalModuleContainer

class BaseSpacer:
    """  Overlay for module functionality """

    def render(self, request=None, using=None, module=None, **kwargs):
        # Render the module
        context = self.get_context_data(module=module, **kwargs)
        template = get_template(self.template_name, using=using)
        rendered_result = template.render(context, request)

        # Return the result as safe
        return mark_safe(rendered_result)

    def get_context_data(self, **kwargs):
        context = kwargs
        return context

    def use(self, **kwargs):
        """
        A method whether the filler should be used in the current context
        :param kwargs: A collection of given arguments from the render method
        :return: A boolean on whether the overlay is valid in this context
        """
        return True


class InsertModuleSpacer(BaseSpacer):
    template_name = "pagedisplay/module_overlays/mf_insert_selection.html"
    script_name = "javascript/filler_insert_module.js"

    def get_context_data(self, prev_module=None, **kwargs):
        context = super(InsertModuleSpacer, self).get_context_data(**kwargs)
        current_container = kwargs['current_container']
        context['container'] = current_container

        # Create a unique id for the radio button
        context['unique_radio_id'] = "insert_filler_selected_"+str(current_container.id)
        if 'forloop' in kwargs.keys():
            context['unique_radio_id'] += str(kwargs['forloop'].get('counter', 0))

        if prev_module:
            pos_low = prev_module.position
            next_module = current_container.basemodule_set.\
                filter(position__gte=prev_module.position).\
                exclude(id=prev_module.id).\
                order_by('position').first()

            if next_module is not None:
                pos_high = next_module.position
            else:
                pos_high = 500
        else:
            # It is before the first in
            next_module = current_container.basemodule_set.order_by('position').first()
            pos_low = 1

            if next_module is not None:
                pos_high = next_module.position
            else:
                pos_high = 500

        insert_position = pos_low + math.ceil((pos_high - pos_low) / 2)

        context['prev_loc'] = pos_low
        context['next_loc'] = pos_high
        context['insert_position'] = insert_position

        return context


class InsertModuleMarkerSpacer(BaseSpacer):
    """ Displays the relative location of the new module """
    template_name = "pagedisplay/module_overlays/mf_insert_selected.html"

    def __init__(self, *args, active_container=None, position=None, **kwargs):
        # Create 'empty' attributes
        self.append_to_end = False
        self.position = position
        # Store the active container (i.e. in which a module will be added)
        self.active_container = active_container

        super(InsertModuleMarkerSpacer, self).__init__(*args, **kwargs)

    def get_context(self, **kwargs):
        context = super(InsertModuleMarkerSpacer, self).get_context(**kwargs)
        context['append_to_end'] = self.append_to_end
        return context

    def use(self, prev_module=None, current_container=None, **kwargs):
        if not super(InsertModuleMarkerSpacer, self).use(**kwargs):
            return False

        if current_container.id != self.active_container.id:
            return False

        if prev_module:
            next_module = self.active_container.basemodule_set. \
                filter(position__gte=prev_module.position). \
                exclude(id=prev_module.id). \
                order_by('position').first()

            if next_module is not None:
                high_check = self.position <= next_module.position
            else:
                high_check = True

            return high_check and self.position > prev_module.position
        else:
            # It is before the first in
            next_module = current_container.basemodule_set.order_by('position').first()

            if next_module is not None:
                return self.position <= next_module.position
            else:
                return True
