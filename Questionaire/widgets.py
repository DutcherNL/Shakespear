from django.forms.widgets import ClearableFileInput


class IconInput(ClearableFileInput):
    template_name = "widgets/icon_input.html"
    icon_height = 80
    icon_width = 80

    def __init__(self, *args, icon_height=None, icon_width=None, **kwargs):
        super(IconInput, self).__init__(*args, **kwargs)
        self.icon_height = icon_height or self.icon_height
        self.icon_width = icon_width or self.icon_width

    def get_context(self, name, value, attrs):
        context = super(IconInput, self).get_context(name, value, attrs)
        icon_dict = {
            'width': self.icon_width,
            'height': self.icon_height
        }
        context['widget'].update({
            'icon': icon_dict
        })
        return context
