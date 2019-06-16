from django.forms.widgets import RadioSelect, Widget


class CustomRadioSelect(RadioSelect):
    template_name = 'snippets/radio.html'
    none_value_string = "None"

    def get_context(self, name, value, attrs):
        context = super(CustomRadioSelect, self).get_context(name, value, attrs)
        context['widget']['type'] = "radio"
        context['widget']['none_value'] = self.none_value_string
        if context['widget']['value'] == ['']:
            context['widget']['none_selected'] = True

        return context

    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data and this widget's name, return the value
        of this widget or None if it's not provided.
        """
        value = super(CustomRadioSelect, self).value_from_datadict(data, files, name)
        if value == self.none_value_string:
            return None
        return value


class InformationDisplayWidget(Widget):
    template_name = 'snippets/widget_text_display.html'

    def get_context(self, name, value, attrs):
        context = super(InformationDisplayWidget, self).get_context(name, value, attrs)
        context['widget']['type'] = "none"
        context['widget']['text'] = value

        return context

