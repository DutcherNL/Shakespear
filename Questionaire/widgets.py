from django.forms.widgets import RadioSelect


class CustomRadioSelect(RadioSelect):
    template_name = 'snippets/radio.html'