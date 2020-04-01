from django.utils.safestring import mark_safe
from django.template.loader import get_template

import math

from .models import ContainerModulePositionalLink

__all__ = ['InsertModuleSpacer', 'InsertModuleMoveSpacer', 'InsertModuleMarkerSpacer']


class BaseSpacer:
    """  Overlay for module functionality """

    def render(self, context=None, **kwargs):
        # Render the module
        request = context['request']
        context['widget'] = self.get_context_data(**kwargs)
        template = get_template(self.template_name, using=context.get('using', None))
        rendered_result = template.render(context, request)

        # Return the result as safe
        return mark_safe(rendered_result)

    def get_context_data(self, prev_module=None, container=None, field_name=None):
        return {
            'container': container,
            'field_name': field_name,
            'prev_module': prev_module,
        }

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
            prev_module_link = prev_module.container_link.first()

            pos_low = prev_module_link.position
            next_module = current_container.module_link. \
                filter(position__gte=prev_module_link.position). \
                exclude(module_id=prev_module.id). \
                order_by('position').first()

            if next_module is not None:
                pos_high = next_module.position
            else:
                pos_high = max(self.local_maximum, prev_module_link.position + self.maximum_overstep)
        else:
            # It is before the first in
            next_module = current_container.module_link.order_by('position').first()
            pos_low = 1

            if next_module is not None:
                pos_high = next_module.position
            else:
                pos_high = self.local_maximum

        return pos_low + math.ceil((pos_high - pos_low) / 2)

    def get_context_data(self, **kwargs):
        context = super(InsertModuleSpacer, self).get_context_data(**kwargs)

        insert_position = self.compute_local_position(context['prev_module'], context['container'])
        context['insert_position'] = insert_position

        # Create a unique id for the radio button
        context['unique_radio_id'] = f"insert_filler_selected_{context['container'].id}_{insert_position}"

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
        self.selected_module_link = selected_module.container_link.first()
        self.rendered_module = None
        super(InsertModuleMoveSpacer, self).__init__()

    def get_context_data(self, **kwargs):
        context = super(InsertModuleMoveSpacer, self).get_context_data(**kwargs)
        prev_module = context.get('prev_module', None)

        if self.rendered_module is None:
            self.rendered_module = self.selected_module.render(**kwargs)
        context['selected_module_layout'] = self.rendered_module

        # Check if this spacer contains the current position of the selected module
        if prev_module is not None and prev_module.id == self.selected_module.id:
            print("Yeah")
            # Change the insert position to represent the current position (in case the module isn't moved)
            context['insert_position'] = self.selected_module_link.position
            # Mark the current version as the original position
            context['start_selected'] = True

        return context

    def use(self, prev_module=None, container=None, **kwargs):
        """
        A method whether the spacer should be used in the current context
        :param prev_module: The module that has been rendered before this gap
        :param kwargs: A collection of given arguments from the render method
        :return: A boolean on whether the overlay is valid in this context
        """
        if prev_module:
            cur_pos = prev_module.container_link.first().position
        else:
            cur_pos = 0

        # If the current position is below the selected position
        # Check if the next module is the selecetd module
        print(f'{cur_pos} - {self.selected_module_link.position}')
        if cur_pos < self.selected_module_link.position:
            next_module_link = container.module_link. \
                filter(position__gt=cur_pos). \
                order_by('position').first()
            if next_module_link:
                if next_module_link.id == self.selected_module_link.id:
                    # The same link is being observed, do not render this module
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
        self.active_container = active_container.get_child()

        super(InsertModuleMarkerSpacer, self).__init__(*args, **kwargs)

    def get_context(self, **kwargs):
        context = super(InsertModuleMarkerSpacer, self).get_context(**kwargs)
        context['append_to_end'] = self.append_to_end
        return context

    def use(self, prev_module=None, container=None, **kwargs):
        if not super(InsertModuleMarkerSpacer, self).use(**kwargs):
            return False

        if container.id != self.active_container.id:
            return False

        if prev_module:
            next_module = self.active_container.module_link. \
                filter(position__gte=prev_module.position). \
                exclude(module_id=prev_module.id). \
                order_by('position').first()

            if next_module is not None:
                high_check = self.position <= next_module.position
            else:
                high_check = True

            return high_check and self.position > prev_module.position
        else:
            # It is before the first in
            next_module = self.active_container.module_link.order_by('position').first()

            if next_module is not None:
                return self.position <= next_module.position
            else:
                return True



