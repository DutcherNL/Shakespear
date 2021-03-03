from django.forms.widgets import *
from django.utils.safestring import mark_safe


__all__ = ["CustomRadioSelect", "InformationDisplayWidget", "IgnorableTextInput", "ExternalDataInputLocal",
           "IgnorableEmailInput", "IgnorableNumberInput", "IgnorableDoubleInput", "CustomMultiSelect"]


class InformationDisplayWidget(Widget):
    """ A widget that does not do anything except display text in between other widgets """
    template_name = 'widgets/widget_text_display.html'

    def get_context(self, name, value, attrs):
        context = super(InformationDisplayWidget, self).get_context(name, value, attrs)
        context['widget']['type'] = "none"
        context['widget']['text'] = value

        return context


class IgnorableInputMixin(object):
    template_name = 'widgets/widget_ignorable_wrapper.html'
    none_name_appendix = "_ignore"

    def __init__(self, *args, empty=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty = empty
        self.is_answered = False

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context['widget']['none_name'] = context['widget']['name'] + self.none_name_appendix
        if context['widget']['value'] == [''] and not self.empty:
            context['widget']['none_selected'] = True

        # Set the non_name in the javascript code
        context['widget']['attrs']['onclick'] = mark_safe(
            context['widget']['attrs']['onclick'].replace('{non_name}', context['widget']['none_name']))

        context['widget']['layout_name'] = super(IgnorableInputMixin, self).template_name

        return context

    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data and this widget's name, return the value
        of this widget or None if it's not provided.
        """
        value = super().value_from_datadict(data, files, name)

        # Determine if the question has been answered, to determine if the empty question has been answered
        if not (value == '' or value is None):
            self.is_answered = True
        else:
            self.is_answered = False

        if self.ignore_value_from_datadict(data, name, value):
            self.is_answered = True
            return None

        return value

    def ignore_value_from_datadict(self, data, name, value):
        """ Determines if the returned result should be ignored """
        ignore_name = name + self.none_name_appendix
        return ignore_name in data

    def build_attrs(self, *args, **kwargs):
        # Remove the required attribute from the html as that blocks going backward
        attrs = super().build_attrs(*args, **kwargs)
        attrs.pop('required', None)

        # Add the javascript code
        attrs['onclick'] = "c = document.getElementById('{non_name}');" \
                           "if (c.checked == true) {c.parentElement.click()}"
        return attrs


class IgnorableTextInput(IgnorableInputMixin, TextInput):
    pass


class IgnorableEmailInput(IgnorableInputMixin, EmailInput):
    pass


class IgnorableNumberInput(IgnorableInputMixin, NumberInput):
    pass


class IgnorableDoubleInput(IgnorableNumberInput):
    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)

        # Add a step
        attrs['step'] = 0.1

        return attrs


class CustomRadioSelect(IgnorableInputMixin, RadioSelect):
    template_name = 'widgets/widget_radio.html'
    input_type = 'radio'
    answer_height = None

    def __init__(self, *args, images=None, **kwargs):
        super(CustomRadioSelect, self).__init__(*args, **kwargs)
        self.images = images or {}

    def get_context(self, name, value, attrs):
        context = super(CustomRadioSelect, self).get_context(name, value, attrs)

        context['widget']['type'] = self.input_type
        context['widget']['images'] = self.images

        return context

    def create_option(self, name, value, *args, **kwargs):
        option = super(CustomRadioSelect, self).create_option(name, value, *args, **kwargs)
        option['image'] = self.images.get(value, None)
        option['answer_height'] = self.answer_height
        return option

    def ignore_value_from_datadict(self, data, name, value):
        """ Determines if the returned result should be ignored """
        ignore_value = name + self.none_name_appendix
        return value == ignore_value


class CustomMultiSelect(IgnorableInputMixin, CheckboxSelectMultiple):
    template_name = 'widgets/widget_q_multi.html'
    answer_height = None

    def __init__(self, *args, images=None, **kwargs):
        super(CustomMultiSelect, self).__init__(*args, **kwargs)
        self.images = images or {}

    def get_context(self, name, value, attrs):
        context = super(CustomMultiSelect, self).get_context(name, value, attrs)

        context['widget']['type'] = self.input_type
        context['widget']['images'] = self.images

        return context

    def create_option(self, name, value, *args, **kwargs):
        option = super(CustomMultiSelect, self).create_option(name, value, *args, **kwargs)
        option['image'] = self.images.get(value, None)
        option['answer_height'] = self.answer_height
        return option

    def ignore_value_from_datadict(self, data, name, value):
        """ Determines if the returned result should be ignored """
        ignore_value = name + self.none_name_appendix
        return ignore_value in value


class ExternalDataInput(Widget):

    def __init__(self, Question, Inquiry, *args, is_hidden=False, **kwargs):
        super(ExternalDataInput, self).__init__(*args, **kwargs)
        self.visible = not is_hidden
        self.is_answered = True

    @property
    def is_hidden(self):
        return not self.visible

    def value_from_datadict(self, data, files, name):
        """
        Actually looks up the data from the external source as defined by the link
        """
        return self.query_data()

    def query_data(self):
        raise NotImplemented()

    def render(self, *args, **kwargs):
        """
        This method normally renders the widget, but this widget retrieves the information from elsewhere
        Therefore it should not be rendered and returns an empty string
        :return: an empty string
        """
        if self.is_hidden:
            return ""
        else:
            result = self.query_data()
            if result is None:
                return "Onbekend"
            return result


class ExternalDataInputLocal(ExternalDataInput):
    visible = True

    def __init__(self, inquiry, external_source_obj, *args, **kwargs):
        super(ExternalDataInput, self).__init__(*args, **kwargs)

        self.external_source = external_source_obj
        self.inquiry = inquiry

    def query_data(self):
        content = self.external_source.get_content(inquiry=self.inquiry)

        return content
