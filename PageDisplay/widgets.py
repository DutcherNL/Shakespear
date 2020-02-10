from django.forms.widgets import NumberInput


class ModulePositionInput(NumberInput):
    template_name = "pagedisplay/widgets/module_position_input.html"
