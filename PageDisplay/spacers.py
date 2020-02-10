from django.utils.safestring import mark_safe
from django.template.loader import get_template

import math

from .models import VerticalModuleContainer

__all__ = ['InsertModuleSpacer', 'InsertModuleMoveSpacer', 'InsertModuleMarkerSpacer']

class BaseSpacer:
    """  Overlay for module functionality """

    def render(self, request=None, using=None, **kwargs):
        # Render the module
        context = self.get_context_data(**kwargs)
        template = get_template(self.template_name, using=using)
        rendered_result = template.render(context, request)

        # Return the result as safe
        return mark_safe(rendered_result)

    def get_context_data(self, **kwargs):
        context = kwargs
        return context

    def use(self, **kwargs):
        """
        A method whether the spacer should be used in the current context
        :param kwargs: A collection of given arguments from the render method
        :return: A boolean on whether the overlay is valid in this context
        """
        return True


class InsertModuleSpacer(BaseSpacer):
    template_name = "pagedisplay/module_overlays/mf_insert_selection.html"
    script_name = "javascript/filler_insert_module.js"

    local_maximum = 200  # the default maximum range
    maximum_overstep = 20  # the step size when the maximum has been reached
    db_maximum = 1000  # the maximum position size on the database

    def compute_local_position(self, prev_module, current_container):
        """ Computes the local position based on the parameters of the given surroundings """
        if prev_module:
            pos_low = prev_module.position
            next_module = current_container.basemodule_set. \
                filter(position__gte=prev_module.position). \
                exclude(id=prev_module.id). \
                order_by('position').first()

            if next_module is not None:
                pos_high = next_module.position
            else:
                pos_high = max(self.local_maximum, prev_module.position + self.maximum_overstep)
        else:
            # It is before the first in
            next_module = current_container.basemodule_set.order_by('position').first()
            pos_low = 1

            if next_module is not None:
                pos_high = next_module.position
            else:
                pos_high = self.local_maximum

        return pos_low + math.ceil((pos_high - pos_low) / 2)

    def get_context_data(self, prev_module=None, container=None, field_name=None, **kwargs):
        context = super(InsertModuleSpacer, self).get_context_data(**kwargs)
        context['insert_container'] = container
        context['insert_field_name'] = field_name

        # Create a unique id for the radio button
        context['unique_radio_id'] = "insert_filler_selected_"+str(container.id)
        if 'forloop' in kwargs.keys():
            context['unique_radio_id'] += str(kwargs['forloop'].get('counter', 0))

        insert_position = self.compute_local_position(prev_module, container)
        context['insert_position'] = insert_position

        return context

    def use(self, prev_module=None, **kwargs):
        if prev_module is not None:
            if prev_module.position >=self.db_maximum:
                return False
        return super(InsertModuleSpacer, self).use(**kwargs)


class InsertModuleMoveSpacer(InsertModuleSpacer):
    template_name = "pagedisplay/module_overlays/mf_move_module.html"

    def __init__(self, selected_module):
        self.selected_module = selected_module
        self.rendered_module = None
        super(InsertModuleMoveSpacer, self).__init__()

    def get_context_data(self, **kwargs):
        context = super(InsertModuleMoveSpacer, self).get_context_data(**kwargs)
        prev_key = kwargs.get('prev_module', None)

        if self.rendered_module is None:
            self.rendered_module = self.selected_module.render(**kwargs)
        context['selected_module_layout'] = self.rendered_module

        # Check if this spacer contains the current position of the selected module
        if prev_key is not None and prev_key.id == self.selected_module.id:
            # Change the insert position to represent the current position (in case the module isn't moved)
            context['insert_position'] = self.selected_module.position
            # Mark the current version as the original position
            context['start_selected'] = True

        return context

    def use(self, prev_module=None, **kwargs):
        """
        A method whether the spacer should be used in the current context
        :param prev_module: The module that has been rendered before this gap
        :param kwargs: A collection of given arguments from the render method
        :return: A boolean on whether the overlay is valid in this context
        """
        if prev_module:
            cur_pos = prev_module.position
        else:
            cur_pos = 0
        # If the current position is below the selected position
        # Check if the next module is the selecetd module
        if cur_pos < self.selected_module.position:
            current_container = kwargs['current_container']
            next_module = current_container.basemodule_set. \
                filter(position__gt=cur_pos). \
                order_by('position').first()
            # Next module is this module, do not render this element
            if next_module.id == self.selected_module.id:
                return False

        return super(InsertModuleMoveSpacer, self).use(prev_module=prev_module, **kwargs)


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



