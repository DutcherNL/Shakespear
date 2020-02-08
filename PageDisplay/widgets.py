from django.utils.safestring import mark_safe
from django.template.loader import get_template


class BaseModuleWidget:
    """ The base for every module widget

    Module Widgets are similar to Django widgets, except they don't necessarly represent input elements and do NOT
    support the features that are related to the input elements. They are merely for displaying and rendering HTML
    elements
    """

    def __init__(self, model):
        self.model = model

    def render(self, request=None, overlay=None, page_id=None, template_engine=None, **kwargs):
        context = self.get_context(request=request, overlay=overlay, page_id=page_id, template_engine=template_engine)
        template = get_template(self.template_name, using=template_engine)
        rendered_result = template.render(context, request)

        return mark_safe(rendered_result)

    def get_context(self, request=None, overlay=None, page_id=None, template_engine=None):
        return {'module': self.model, 'page_id': page_id, "overlay": overlay, 'template_engine': template_engine}


class TitleWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_title.html"


class TextWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_text.html"


class ImageWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_image.html"

    def get_context(self, request=None, **kwargs):
        context = super(ImageWidget, self).get_context(request, **kwargs)
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

