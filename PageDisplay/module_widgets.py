from django.utils.safestring import mark_safe
from django.template.loader import get_template


class BaseModuleWidget:
    """ The base for every module widget

    Module Widgets are similar to Django widgets, except they don't necessarly represent input elements and do NOT
    support the features that are related to the input elements. They are merely for displaying and rendering HTML
    elements
    """
    # Use this parameter to obtain data from the global context as kwargs in the get_context_data method
    # This is called in the BasicModuleMixin class and only applies for basic modules
    use_from_context = []

    def __init__(self, model):
        self.model = model

    def render(self, request=None, context=None, **kwargs):
        context = context or {}
        context['widget'] = self.get_context_data(request=request, **kwargs)

        template = get_template(self.template_name, using=context.get('template_engine', None))
        rendered_result = template.render(context, request)

        return mark_safe(rendered_result)

    def get_context_data(self, request=None, **kwargs):
        return {'module': self.model,
                **kwargs}


class VerticalContainerWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_vertical_container.html"


class TitleWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_title.html"


class TextWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_text.html"


class ImageWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_image.html"

    def get_context_data(self, request=None, **kwargs):
        context = super(ImageWidget, self).get_context_data(request, **kwargs)
        img_mode = self.model.mode
        if img_mode == "auto":
            context['size'] = "contain"
        elif img_mode == "full":
            context['size'] = "cover"
        else:
            context['size'] = img_mode

        return context


class WhiteSpaceWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_whitespace.html"

