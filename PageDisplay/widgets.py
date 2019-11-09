from django.utils.safestring import mark_safe
from django.forms.renderers import get_default_renderer
from django.template.loader import get_template, TemplateDoesNotExist


class BaseModuleWidget:
    """ The base for every module widget

    Module Widgets are similar to Django widgets, except they don't necessarly represent input elements and do NOT
    support the features that are related to the input elemetns. They are merely for displaying and rendering HTML
    elements
    """

    def __init__(self, model):
        self.model = model

    def render(self, request=None, using=None):
        context = self.get_context(request=request)
        template = get_template(self.template_name, using=using)
        rendered_result = template.render(context, request)

        return mark_safe(rendered_result)

    def get_context(self, request=None):
        return {'module': self.model}


class TitleWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_title.html"


class TextWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_text.html"


class ImageWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_image.html"

    def get_context(self, request=None):
        context = super().get_context()
        context['image'] = self.model.image
        context['height'] = 100
        return context

