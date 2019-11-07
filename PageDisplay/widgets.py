from django.utils.safestring import mark_safe
from django.forms.renderers import get_default_renderer


class BaseModuleWidget:
    """ The base for every module widget

    Module Widgets are similar to Django widgets, except they don't necessarly represent input elements and do NOT
    support the features that are related to the input elemetns. They are merely for displaying and rendering HTML
    elements
    """

    def __init__(self, model):
        self.model = model

    def render(self, renderer=None):
        context = self.get_context()
        if renderer is None:
            renderer = get_default_renderer()
        return mark_safe(renderer.render(self.template_name, context))

    def get_context(self):
        return {'module': self.model}


class TitleWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_title.html"


class TextWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_text.html"


class ImageWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_image.html"

    def get_context(self):
        context = super().get_context()
        context['image'] = self.model.image
        context['height'] = 100
        return context

