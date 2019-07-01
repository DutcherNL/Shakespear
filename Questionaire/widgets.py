from django.forms.widgets import RadioSelect, Input


class CustomRadioSelect(RadioSelect):
    template_name = 'snippets/widget_radio.html'
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


class IgnorableInput(Input):
    template_name = 'snippets/widget_text.html'
    none_name_appendix = "_ignore"

    def __init__(self, *args, **kwargs):
        super(IgnorableInput, self).__init__(*args, **kwargs)
        self.required = kwargs.get('required', False)

    def get_context(self, name, value, attrs):
        # Filter the required attribute in args and make sure it aligns
        if attrs.get('required', False) != self.required:
            if self.required:
                attrs['required'] = True
            else:
                attrs.pop('required')

        context = super(IgnorableInput, self).get_context(name, value, attrs)

        context['widget']['none_name'] = context['widget']['name'] + self.none_name_appendix
        if context['widget']['value'] == ['']:
            context['widget']['none_selected'] = True

        return context

    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data and this widget's name, return the value
        of this widget or None if it's not provided.
        """
        value = super(CustomRadioSelect, self).value_from_datadict(data, files, name)

        ignore = data.get(name + self.none_name_appendix, False)
        if ignore:
            return None
        
        return value


class IgnorableEmailInput(IgnorableInput):
    input_type = 'email'
