from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse

from .module_registry import registry
from PageDisplay import module_widgets, renderers

# Create your models here.
__all__ = ['ModuleContainer', 'VerticalModuleContainer',
           'Page', 'BaseModule']


class ModuleContainer(models.Model):
    """
    Contains a collection of modules
    
    A container could technically nest other containers createing a deep rooted structure.
    """

    def get_context_data(self, request=None, overlay=None, page_id=None, **kwargs):
        context = {'request': request,
                   'modules': self.basemodule_set.order_by('position'),
                   'overlay': overlay,
                   'page_id': page_id,
                   'current_container': self,
                   'renderer': kwargs.get('renderer', None),
                   'spacer': kwargs.get('spacer', None),
                   'active_container': kwargs.get('active_container', None),
                   'selected_module': kwargs.get('selected_module', None),
                   'url_kwargs': kwargs.get('url_kwargs', None),
                   'template_engine':  kwargs.get('template_engine', None),
                   }

        return context
    
    def render(self, **kwargs):
        """
        Calls the render method in the correct subclass
        'this' must be a registered subclass of ModuleContainer otherwise it will not detect the correct subclass. 
        :param kwargs: A collection of arguments used by the modules.
        :return: A rendered HTML Template
        """
        child = self.get_as_child()
        if child == self and self.__class__ == ModuleContainer:
            return "Base container :/"
        return child._render(**kwargs)

    def _render(self, request=None, **kwargs):
        """
        Render the modules inside the container in a vertical manner
        :param request: The Request object
        :param kwargs: Other kwarg arguments that can be used somewhere in the render process (= contents of context)
        :return:
        """
        # Get the template
        from django.template.loader import get_template
        template = get_template(self.template_name, using=kwargs.get('template_engine', None))

        # Get the context
        context = self.get_context_data(request, **kwargs)
        # Renders the template with the context data.
        return template.render(context)

    def get_as_child(self):
        """ Returns the child object of this class"""
        # Loop over all children
        for child in self.__class__.__subclasses__():
            # If the child object exists
            if child.objects.filter(id=self.id).exists():
                return child.objects.get(id=self.id).get_as_child()
        return self

    @property
    def page(self):
        return self.page_set.all()[0]


class VerticalModuleContainer(ModuleContainer):
    """ Renders the modules in a vertical fashion """
    template_name = 'pagedisplay/modules/module_vert_container.html'


class Page(models.Model):
    """
    A visible page, contains a unique url to display the page

    Is a wrapper of sorts for root module container contained in layout
    """
    layout = models.ForeignKey(ModuleContainer, on_delete=models.PROTECT, blank=True)
    name = models.CharField(max_length=63)

    option_fields = ['name']
    renderer = renderers.BasePageRenderer

    def __init__(self, *args, **kwargs):
        # If a different container class is defined, create that container class object
        if 'layout' in kwargs.keys():
            if isinstance(kwargs.get('layout'), type):
                # If layout is a class, initiate and create the class model instance
                kwargs['layout'] = kwargs['layout'].objects.create()
        super(Page, self).__init__(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('pages:view_page', kwargs={'page_id': self.id})

    def save(self, *args, **kwargs):
        try:
            if self.layout is None:
                # If there is no container, default to a basic container
                self.layout = VerticalModuleContainer.objects.create()
        except ModuleContainer.DoesNotExist:
            self.layout = VerticalModuleContainer.objects.create()

        return super(Page, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_as_child(self):
        """ Returns the child object of this class"""
        # Loop over all children
        for child in self.__class__.__subclasses__():
            # If the child object exists
            if child.objects.filter(id=self.id).exists():
                return child.objects.get(id=self.id).get_as_child()
        return self

    def render(self, **kwargs):
        """
        Calls the render method in the correct subclass
        'this' must be a registered subclass of ModuleContainer otherwise it will not detect the correct subclass.
        :param kwargs: A collection of arguments used by the modules.
        :return: A rendered HTML Template
        """
        child = self.get_as_child()
        return child._render(**kwargs)

    def _render(self, **kwargs):
        """
        Render the modules inside the container in a vertical manner
        :param request: The Request object
        :param kwargs: Other kwarg arguments that can be used somewhere in the render process (= contents of context)
        :return:
        """
        # Give priority if the renderer is in the kwarg arguments
        renderer = kwargs.pop('renderer', self.renderer)
        return renderer(page=self).render(**kwargs)

    def add_basic_module(self, moduleclass, **kwargs):
        """
        Adds the basic module to the layout. Should be used to add some default modules without having to concern about
        the structure of the page.
        :param moduleclass: The class that the module needs to be
        :param kwargs: The keyword arguments used for module class initiation
        :return: Returns the created module
        """
        assert 'information' not in kwargs.keys()

        module = moduleclass(information=self.layout, **kwargs)
        module.save()
        return module


class BaseModule(models.Model):
    """
    The basis for page modules

    A module is a small puzzlepiece from which pages can be build. E.g. Titles, text, images.
    More complex features like interactive plugins are also possible.
    """
    # A verbose name for the specific module
    verbose = "-Abstract module-"
    # A unique number to identify the type of module
    _type_id = 0

    # Database fields
    information = models.ForeignKey(ModuleContainer, on_delete=models.PROTECT)
    position = models.PositiveIntegerField(default=999)
    _type = models.PositiveIntegerField() # A number to optimise the search for the specific module table.

    @property
    def type(self):
        return self.verbose

    def get_child(self):
        """
        Returns the child instance of the base module
        :return:
        """
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

    def render(self, widget=None, request=None, using=None, overlay=None, page_id=None, **kwargs):
        """
        Renders the module
        :param widget: The widget the module uses. Defaults if none is given
        :param request: The Request object
        :param using: The template engine
        :param overlay: The ModuleOverlay instance
        :param page_id: The id of the page
        :param kwargs:
        :return:
        """
        # Get the child as deep as possible
        child = self.get_child()
        # Load the widget
        widget_inst = child._init_widget(widget)
        print(f'widget: {widget_inst}')
        # Load the widget and render it
        return child._render(widget_inst, request, **kwargs)

    @staticmethod
    def _render(widget, request, **kwargs):
        return widget.render(request, **kwargs)

    def get_fixed_properties(self):
        """ Get fixed properties to display in the fixed properties window """
        properties = [('type', self.type), ('position', self.position)]
        return properties

    def save(self, **kwargs):
        # Guarantee that the _type_id is stored correctly on all objects
        self._type = self._type_id
        super(BaseModule, self).save(**kwargs)


class BasicModuleMixin:
    """ A Mixin that overrides the _render method to limit the arguments in the widget render method """

    @staticmethod
    def _render(widget, request, overlay=None, page_id=None, template_engine=None, **kwargs):
        # **kwargs catches all not relevant arguments
        return widget.render(request, overlay=overlay, page_id=page_id, template_engine=template_engine)


class TitleModule(BasicModuleMixin, BaseModule):
    """ A module that renders a title """
    verbose = "Title"
    widget = module_widgets.TitleWidget
    _type_id = 1

    title = models.CharField(max_length=127)
    size = models.PositiveIntegerField(default=1, help_text="The level of the title 1,2,3... maz 5")
    css = models.CharField(max_length=256, help_text="CSS classes in accordance with Bootstrap",
                           null=True, blank=True, default="")


class TextModule(BasicModuleMixin, BaseModule):
    """ A module that renders simple text """
    verbose = "Text"
    _type_id = 2
    widget = module_widgets.TextWidget

    text = models.TextField()
    css = models.CharField(max_length=256, help_text="CSS classes in accordance with Bootstrap",
                           null=True, blank=True, default="")

    def __str__(self):
        return self.text


class ImageModule(BasicModuleMixin, BaseModule):
    """ A module that displays an image """
    verbose = "Image"
    _type_id = 3
    widget = module_widgets.ImageWidget

    image = models.ImageField()
    caption = models.CharField(max_length=256, null=True, blank=True, default="")
    height = models.PositiveIntegerField(default=100)

    mode_choices = [
        ('auto', "Display full image"),
        ('full', "Cover image")
    ]
    mode = models.SlugField(choices=mode_choices, default="auto")
    css = models.CharField(max_length=256, help_text="CSS classes in accordance with Bootstrap",
                           null=True, blank=True, default="")


class WhiteSpaceModule(BasicModuleMixin, BaseModule):
    _type_id = 4
    widget = module_widgets.WhiteSpaceWidget
    verbose = "Whitespace"

    height = models.PositiveIntegerField(default=100, validators=[
        MinValueValidator(limit_value=25),
        MaxValueValidator(limit_value=1000)
    ])


registry.register(TitleModule)
registry.register(TextModule)
registry.register(ImageModule)
registry.register(WhiteSpaceModule)
