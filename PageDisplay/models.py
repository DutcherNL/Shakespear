from django.db import models
from django.urls import reverse

from .module_registry import registry
from PageDisplay import widgets

# Create your models here.


class ModuleContainer(models.Model):
    def render(self, overlay=None, inf_id=None, request=None):
        if self.verticalmodulecontainer:
            return self.verticalmodulecontainer.render(overlay, inf_id, request)
        return "Base container :/"


class VerticalModuleContainer(ModuleContainer):
    template_name = 'pagedisplay/modules/module_vert_container.html'

    def get_context_data(self, request=None):
        context = {'request': request,
                   'modules': self.basemodule_set.order_by('position')}
        return context

    def render(self, overlay=None, inf_id=None, request=None):
        from django.template.loader import get_template

        template = get_template(self.template_name)
        context = self.get_context_data(request)
        context['overlay'] = overlay
        context['inf_id'] = inf_id
        return template.render(context)  # Renders the template with the context data.


class Page(models.Model):
    layout = models.ForeignKey(ModuleContainer, on_delete=models.PROTECT)
    name = models.CharField(max_length=63)

    def get_absolute_url(self):
        return reverse('info_page', kwargs={'inf_id': self.id})


class BaseModule(models.Model):
    """
    A module to create information
    """
    verbose = "-Abstract module-"
    _type_id = 0
    information = models.ForeignKey(ModuleContainer, on_delete=models.PROTECT)
    position = models.PositiveIntegerField(default=999)
    _type = models.PositiveIntegerField()

    @property
    def type(self):
        return self.verbose

    def __init__(self, *args, **kwargs):
        super(BaseModule, self).__init__(*args, **kwargs)

    def get_child(self):
        # Get the module class from the module registry
        child_class = registry.get_module(self._type)

        # Retrieve the child through the class objects
        # Django inheritance maintains object id of the parent in the children
        child_obj = child_class.objects.get(id=self.id)

        return child_obj

    def _init_widget(self, widget=None):
        """ Initialise the widget object """
        widget = widget or self.widget
        if isinstance(widget, type):
            widget = widget(model=self)
        return widget

    def render(self, widget=None, request=None, using=None, overlay=None, inf_id=None):
        # Get the child as deep as possible
        child = self.get_child()
        # Load the widget and render it
        return child._init_widget(widget).render(request=request, using=using, overlay=overlay, inf_id=inf_id)

    def get_fixed_properties(self):
        """ Get fixed properties to display in the fixed properties window """
        properties = [('type', self.type), ('position', self.position)]
        return properties

    def save(self, **kwargs):
        # Guarantee that the _type_id is stored correctly on all objects
        self._type = self._type_id
        super(BaseModule, self).save(**kwargs)


class TitleModule(BaseModule):
    verbose = "Title"
    widget = widgets.TitleWidget
    _type_id = 1

    title = models.CharField(max_length=127)
    size = models.PositiveIntegerField(default=1, help_text="The level of the title 1,2,3... maz 5")
    css = models.CharField(max_length=256, help_text="CSS classes in accordance with Bootstrap",
                           null=True, blank=True, default="")


class TextModule(BaseModule):
    verbose = "Text"
    _type_id = 2
    widget = widgets.TextWidget

    text = models.TextField()
    css = models.CharField(max_length=256, help_text="CSS classes in accordance with Bootstrap",
                           null=True, blank=True, default="")

    def __str__(self):
        return self.text


class ImageModule(BaseModule):
    verbose = "Image"
    _type_id = 3
    widget = widgets.ImageWidget

    image = models.ImageField()
    caption = models.CharField(max_length=256, null=True, blank=True, default="")
    height = models.PositiveIntegerField(default=100)
    css = models.CharField(max_length=256, help_text="CSS classes in accordance with Bootstrap",
                           null=True, blank=True, default="")


registry.register(TitleModule)
registry.register(TextModule)
registry.register(ImageModule)
