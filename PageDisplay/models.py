from django.db import models
from django.utils.safestring import mark_safe
from django.forms.renderers import get_default_renderer
from django.urls import reverse

from .module_registry import registry

# Create your models here.


class Information(models.Model):
    name = models.CharField(max_length=63)

    template_name = 'page_info_display.html'

    def get_absolute_url(self):
        return reverse('info_page', kwargs={'inf_id': self.id})

    def __str__(self):
        return self.name

    def get_context_data(self):
        context = {}
        context['modules'] = self.basemodule_set.order_by('position')
        return context

    def render(self):
        from django.template.loader import get_template

        template = get_template(self.template_name)
        context = self.get_context_data()
        return template.render(context)  # Renders the template with the context data.


class BaseModule(models.Model):
    """
    A module to create information
    """
    verbose = "-Abstract module-"
    _type_id = 0
    information = models.ForeignKey(Information, on_delete=models.PROTECT)
    position = models.PositiveIntegerField(default=999)

    _types = (
        (1, "titlemodule"),
        (2, "textmodule"),
        (3, "imagemodule"),
    )
    _type = models.PositiveIntegerField()
    @property
    def type(self):
        return self.verbose

    def get_child(self):
        class_type = None
        # Get the correct tuple from the list
        for tuple in self._types:
            if tuple[0] == self._type:
                class_type = tuple[1]

        new_obj = getattr(self, class_type)
        return new_obj

    def render(self):
        return self.get_child().render_field()

    def render_field(self):
        context = self.get_context()
        renderer = get_default_renderer()
        return mark_safe(renderer.render(self.template_name, context))

    def get_context(self):
        return {'module': self}

    def get_fixed_properties(self):
        properties = [('type', self.type), ('position', self.position)]
        return properties

    def save(self, **kwargs):
        self._type = self._type_id
        super(BaseModule, self).save(**kwargs)


class TitleModule(BaseModule):
    verbose = "Title"
    _type_id = 1

    template_name = "pagedisplay/modules/module_title.html"

    title = models.CharField(max_length=127)
    size = models.PositiveIntegerField(default=1, help_text="The level of the title 1,2,3... maz 5")
    css = models.CharField(max_length=256, help_text="CSS classes in accordance with Bootstrap",
                           null=True, blank=True, default="")


class TextModule(BaseModule):
    verbose = "Text"
    _type_id = 2

    template_name = "pagedisplay/modules/module_text.html"
    text = models.TextField()
    css = models.CharField(max_length=256, help_text="CSS classes in accordance with Bootstrap",
                           null=True, blank=True, default="")

    def __str__(self):
        return self.text


class ImageModule(BaseModule):
    verbose = "Image"
    _type_id = 3

    template_name = "pagedisplay/modules/module_image.html"
    image = models.ImageField()

    def get_context(self):
        context = super(ImageModule, self).get_context()
        context['image'] = self.image
        context['height'] = 100
        return context


registry.register(TitleModule)
registry.register(TextModule)
