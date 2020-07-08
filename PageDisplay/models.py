from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse

from .module_registry import registry
from PageDisplay import module_widgets, renderers

# Create your models here.


class Page(models.Model):
    """
    A visible page, contains a unique url to display the page

    Is a wrapper of sorts for root module container contained in layout
    """
    root_module = models.ForeignKey('BaseModule', on_delete=models.CASCADE, blank=True, null=True)
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
            if self.root_module is None:
                # If there is no container, default to a basic container
                self.root_module = VerticalContainerModule.objects.create()
        except VerticalContainerModule.DoesNotExist:
            self.root_module = VerticalContainerModule.objects.create()

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
        renderer = kwargs.pop('renderer', None) or self.renderer
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

        module = moduleclass(**kwargs)
        module.save()
        end_position = ContainerModulePositionalLink.objects.filter(container=self.root_module)\
            .order_by('position').last()
        if end_position:
            end_position = end_position.position + 5
        else:
            end_position = 100

        ContainerModulePositionalLink.objects.create(container=self.root_module,
                                                     module=module,
                                                     position=end_position)
        # Todo, correct position in line with approach of inserting modules in GUI
        return module


class BaseModule(models.Model):
    """
    The basis for page modules

    A module is a small puzzlepiece from which pages can be build. E.g. Titles, text, images.
    More complex features like interactive plugins are also possible.
    """
    # DATABASE FIELDS
    # A number to optimise the search for the specific module table.
    _type = models.PositiveIntegerField()

    # OTHER CONSTANTS
    # A verbose name for the specific module
    verbose = "-Abstract module-"
    # A unique number to identify the type of module
    _type_id = 0

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

    def render(self, widget=None, request=None, **kwargs):
        """
        Renders the module
        :param widget: The widget the module uses. Defaults if none is given
        :param request: The Request object
        :param kwargs:
        :return:
        """
        # Get the child as deep as possible
        child = self.get_child()
        # Load the widget
        widget_inst = child._init_widget(widget)
        # Load the widget and render it
        return child._render(widget_inst, request, **kwargs)

    @staticmethod
    def _render(widget, request, **kwargs):
        return widget.render(request, context=kwargs)

    def get_fixed_properties(self):
        """ Get fixed properties to display in the fixed properties window """
        properties = [('type', self.type)]
        return properties

    def save(self, **kwargs):
        # Guarantee that the _type_id is stored correctly on all objects
        self._type = self._type_id
        super(BaseModule, self).save(**kwargs)

    def get_modules(self, filter_class_type=None, filter_id=None, exclude_self=False):
        """
        Returns a list of all modules.
        :param exclude_self: Whether this instance itself should be included
        :param filter_id: The id that needs to be searched (if used it ignores filter_class_type)
        :param filter_class_type: Filters for a specific class type only
        :return: A list of all modules that apply to the query
        """
        if exclude_self:
            return []

        if filter_id:
            if self.id == filter_id:
                return [self]
            else:
                return []

        if filter_class_type:
            if isinstance(self, filter_class_type):
                return [self]
            else:
                return []
        else:
            return [self]


class ContainerModuleMixin:
    """ Superclass for basic container modules
    A ContainerModule is an advanced level module that can contain other modules
    """


class OrderedContainerModule(ContainerModuleMixin, BaseModule):
    module_list = models.ManyToManyField(BaseModule,
                                         through='ContainerModulePositionalLink',
                                         through_fields=('container', 'module'),
                                         related_name='container')

    def get_sub_modules(self):
        """
        Returns a list of all sub modules
        :return: A list of all modules it contains
        """
        return self.get_modules(exclude_self=True)

    def get_modules(self, filter_class_type=None, filter_id=None, exclude_self=False):
        """
        Returns a list of all modules including itself that it contains. Extended because it contains modules
        :param filter_id: The id that needs to be searched (if used it ignores filter_class_type
        :param filter_class_type:
        :return: A list of the modules that were applicable
        """

        if filter_id:
            link = self.module_link.filter(id=filter_id).first()
            if link:
                return [link.module.get_child()]
            elif self.id == filter_id:
                return [self]

        # Add all contained modules and add them to the list
        modules = []
        for module_link in self.module_link.order_by('position'):
            modules.extend(module_link.module.get_child().get_modules(
                filter_class_type=filter_class_type,
                filter_id=filter_id,
                exclude_self=False)
            )

        modules.extend(super(OrderedContainerModule, self).get_modules(
            filter_class_type=filter_class_type,
            filter_id=filter_id,
            exclude_self=exclude_self)
        )
        return modules


class ContainerModulePositionalLink(models.Model):
    """ Illustrates a link between a module container and its modules"""
    container = models.ForeignKey(OrderedContainerModule, on_delete=models.PROTECT, related_name='module_link')
    position = models.PositiveIntegerField(default=999)
    module = models.ForeignKey(BaseModule, on_delete=models.CASCADE, related_name='container_link')


class VerticalContainerModule(OrderedContainerModule):
    widget = module_widgets.VerticalContainerWidget
    _type_id = 10


class BasicModuleMixin:
    """ A Mixin that overrides the _render method to limit the arguments in the widget render method """

    @staticmethod
    def _render(widget, request, overlay=None, page_id=None, template_engine=None, **kwargs):
        # **kwargs catches all not relevant arguments
        # Construct local subset from global context
        # This approach is used to prevent sudden adjustments in the global context_data
        local_context = {}
        for kwarg_name in widget.use_from_context:
            local_context[kwarg_name] = kwargs.get(kwarg_name, None)

        return widget.render(request,
                             overlay=overlay,
                             page_id=page_id,
                             template_engine=template_engine,
                             **local_context)


class TitleModule(BasicModuleMixin, BaseModule):
    """ A module that renders a title """
    verbose = "Title"
    widget = module_widgets.TitleWidget
    _type_id = 1

    title = models.CharField(max_length=127)
    size = models.PositiveIntegerField(default=1, help_text="The level of the title 1,2,3... maz 5")
    css = models.CharField(max_length=256, help_text="CSS classes in accordance with Bootstrap",
                           null=True, blank=True, default="")

    def __str__(self):
        return self.title


class TextModule(BasicModuleMixin, BaseModule):
    """ A module that renders simple text """
    verbose = "Text"
    _type_id = 2
    widget = module_widgets.TextWidget

    text = models.TextField()
    css = models.CharField(max_length=256, help_text="CSS classes in accordance with Bootstrap",
                           null=True, blank=True, default="")

    def __str__(self):
        str = self.text[:40]
        max_length = 40
        if len(self.text) > max_length:
            str = self.text[:max_length]
            str = str[:str.rfind(' ')]
            str += '...'
        return str


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


registry.register(VerticalContainerModule, in_default=False)
registry.register(TitleModule)
registry.register(TextModule)
registry.register(ImageModule)
registry.register(WhiteSpaceModule)


from PageDisplay.modules.modules import *