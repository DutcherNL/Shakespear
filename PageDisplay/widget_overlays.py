from django.utils.safestring import mark_safe
from django.template.loader import get_template


class BaseWidgetOverlay:
    """  Overlay for module functionality """

    def render(self, request=None, using=None, module=None):
        context = self.get_context(request=request)
        template = get_template(self.template_name, using=using)
        rendered_result = template.render(context, request)

        return mark_safe(rendered_result)

    def get_context(self, request=None, module=None):
        return {'module': self.model}


class ModuleSelectOverlay(BaseWidgetOverlay):
    template_name = "pagedisplay/modules/module_title.html"