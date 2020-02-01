from django.views.generic import TemplateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Page, BaseModule, ModuleContainer
from .forms import build_moduleform, AddModuleForm
from .widget_overlays import ModuleSelectOverlay, ModuleEditOverlay, ModuleAddOverlay
from . import reverse_ns

# ------------------------------------ """
# ------- Pages Overview Pages ------- """
# ------------------------------------ """


class PageOverview(LoginRequiredMixin, ListView):
    model = Page
    context_object_name = "pages"
    template_name = "pagedisplay/pages_overview.html"

# ------------------------------------ """
# -------- Page Display Pages -------- """
# ------------------------------------ """


class PageMixin:
    """ Mixin for Page Views

    Params:
    page: The page object that the view processes
    """
    page = None
    site = None
    extends = 'base_with_body.html'
    init_view_params = None
    header_buttons = {}

    def __init__(self, *args, site=None, extends=None, url_kwargs=None, **kwargs):
        self.site = site
        self.url_kwargs = url_kwargs
        self.extends = extends or self.extends
        self.header_buttons = kwargs.pop('header_buttons', self.header_buttons)
        self.init_view_params = kwargs.pop('init_view_params', self.init_view_params)
        super(PageMixin, self).__init__(*args, **kwargs)

    def dispatch(self, *args, **kwargs):
        self.init_params(**kwargs)
        return super(PageMixin, self).dispatch(*args, **kwargs)

    def init_params(self, **kwargs):
        if self.init_view_params is not None:
            self.init_view_params(self, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page'] = self.page
        context['page_id'] = self.page.id
        context['extends'] = self.extends
        context['header_buttons'] = self.header_buttons
        context['url_kwargs'] = self.url_kwargs(self)
        return context

    @staticmethod
    def url_kwargs(self):
        """ Gets the url_kwargs used when reversing urls """
        # This should be overwritten by the site, but is here as a requirement when setting up views
        raise KeyError("url_kwargs has not been inserted from the site level")


class PageInfoView(PageMixin, TemplateView):
    """ Displays a page the normal way """
    template_name = "pagedisplay/page_info_display.html"

    def init_params(self, **kwargs):
        super(PageInfoView, self).init_params(**kwargs)

        if self.site is not None:
            # Create the Edit Page button
            namespace = self.request.resolver_match.namespace
            self.header_buttons['Edit Page'] = reverse(namespace+':edit_page', kwargs=kwargs, current_app=namespace)


class PageEditMixin(LoginRequiredMixin, PageMixin):
    """ A mixin for the page editing back-end """
    pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['overlay'] = self.get_overlay()
        context['active_container'] = self.get_active_container()
        return context

    def get_overlay(self):
        """ Returns the initiated overlay object used in the view """
        try:
            # Enable more flexible mixing ordering by checking the parent
            return super().get_overlay()
        except AttributeError:
            return None

    def get_active_container(self):
        """ Returns the active (selected) container in which work is currently done """
        try:
            # Enable more flexible mixing ordering by checking the parent
            return super().get_active_container()
        except AttributeError:
            return self.page.layout

    def init_params(self, **kwargs):
        super(PageEditMixin, self).init_params(**kwargs)
        print("Step B")

        if self.site is not None:
            # Create the View Page button
            namespace = self.request.resolver_match.namespace
            self.header_buttons['View Page'] = reverse(namespace+':view_page',
                                                       kwargs={'tech_id': kwargs.get('tech_id')},
                                                       current_app=namespace)


class PageAlterView(PageEditMixin, TemplateView):
    """ The root for the page alteration """
    template_name = 'pagedisplay/page_edit_page.html'

    def get_overlay(self):
        return ModuleSelectOverlay()


class PageAlterSettingsView(PageEditMixin, UpdateView):
    """ Contains a form for page settings """
    template_name = 'pagedisplay/page_edit_settings.html'
    fields = ['name']
    model = Page

    def get_object(self, queryset=None):
        return self.page

    def get_success_url(self):
        return reverse_ns(self.request, 'edit_page', kwargs=self.url_kwargs(self))


class PageAddModuleView(PageEditMixin, TemplateView):
    """ View to add modules
    Adding a module contains two steps: first, selection of the module type this is done in the 'root_form'
    Then the details are added through the 'module_form' This latter uses a post method
    """
    template_name = 'pagedisplay/page_edit_add_module.html'

    def __init__(self, *args, **kwargs):
        super(PageAddModuleView, self).__init__(*args, **kwargs)
        # Create empty parameters that will be used later
        self.position = None
        self.container = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.container = ModuleContainer.objects.get(pk=self.kwargs['container_id'])
        context['container'] = self.container

        # If there are no get parameters, initiate the root_form, otherwise. Get those paramaters and check validity
        if len(self.request.GET) == 0:
            root_form = AddModuleForm(container=self.page.layout, site=self.site)
        else:
            root_form = AddModuleForm(container=self.page.layout, site=self.site, data=self.request.GET)

            if root_form.is_valid():
                # Basic parameters are valid so hide the root_form from now on.
                instance = root_form.get_instance()
                self.position = instance.position
                root_form.make_hidden()
                # Initiate the module form from the root_form instance
                context['module_form'] = build_moduleform(instance=instance)

        context['root_form'] = root_form

        # Get the item it is placed in front of:
        if self.position:
            context['overlay'].position = self.position

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        # Construct the root form
        root_form = AddModuleForm(container=self.page.layout, data=self.request.POST, files=self.request.FILES)
        context['root_form'] = root_form

        if root_form.is_valid():
            # Root form is valid, construct module_form
            instance = root_form.get_instance()
            module_form = build_moduleform(instance=instance, data=request.POST, files=self.request.FILES)

            if module_form.is_valid():
                # Module_form is valid. Save the module and go back to the edit page
                module_form.save()
                return HttpResponseRedirect(reverse_ns(self.request, 'edit_page', kwargs=self.url_kwargs(self)))

            context['module_form'] = module_form

        return self.render_to_response(context)

    def get_overlay(self):
        return ModuleAddOverlay(active_container=self.get_active_container())


class ModuleEditMixin:
    """ A mixin for module alterations """
    selected_module = None

    def dispatch(self, request, *args, **kwargs):
        self.selected_module = BaseModule.objects.get(id=kwargs['module_id']).get_child()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_module'] = self.selected_module
        return context

    def get_overlay(self):
        return ModuleEditOverlay()

    def get_active_container(self):
        return self.selected_module.information

    def init_params(self, **kwargs):
        super(ModuleEditMixin, self).init_params(**kwargs)

        # Create the Edit Page button
        namespace = self.request.resolver_match.namespace

        kwargs.pop('module_id', None)
        self.header_buttons['Edit Page'] = reverse(namespace+':edit_page', kwargs=kwargs, current_app=namespace)


class ModuleEditBase(ModuleEditMixin, PageEditMixin):
    """ The general overlap for all module edit views """
    pass


class PageAlterModuleView(ModuleEditBase, UpdateView):
    """ Adjust the details of a given module """
    template_name = 'pagedisplay/page_edit_module.html'
    selected_module = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = build_moduleform(instance=self.selected_module)
        return context

    def get_object(self, queryset=None):
        return self.selected_module

    def get_success_url(self):
        return reverse_ns(self.request, 'edit_page', kwargs=self.url_kwargs(self))

    def get_form_class(self):
        return build_moduleform(instance=self.selected_module, get_as_class=True)


class PageDeleteModuleView(ModuleEditBase, DeleteView):
    model = BaseModule
    selected_module = None
    template_name = "pagedisplay/page_edit_module_delete.html"

    def get_object(self, queryset=None):
        return self.selected_module

    def get_success_url(self):
        return reverse_ns(self.request, 'edit_page', kwargs=self.url_kwargs(self))
