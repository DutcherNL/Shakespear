import copy

from django.views.generic import TemplateView, UpdateView, DeleteView, FormView
from django.views.generic.list import ListView
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Page, BaseModule
from .forms import build_moduleform, AddModuleForm, ModuleLinkForm
from .overlays import *
from .spacers import *
from . import reverse_ns

# ------------------------------------ """
# ------- Pages Overview Pages ------- """
# ------------------------------------ """


class PageOverview(ListView):
    context_object_name = "pages"
    template_name = "pagedisplay/pages_overview.html"
    site = None

    def get_queryset(self):
        # Call the queryset of the site instead of the one in ListView as that allows more versatility
        return self.site.get_queryset()

    def dispatch(self, request, *args, **kwargs):
        # Check access
        if not self.site.can_access(request, self):
            return HttpResponseForbidden("You are not allowed to access this page")

        return super(PageOverview, self).dispatch(request, *args, **kwargs)

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

    def dispatch(self, request, *args, **kwargs):
        self.init_params(**kwargs)

        # Check access
        if not self.site.can_access(request, self):
            return HttpResponseForbidden("You are not allowed to access this page")

        return super(PageMixin, self).dispatch(request, *args, **kwargs)

    def init_params(self, **kwargs):
        if self.init_view_params is not None:
            self.init_view_params(self, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page'] = self.page
        context['page_id'] = self.page.id
        context['extends'] = self.extends
        context['header_buttons'] = self.prep_buttons(self.header_buttons)
        context['url_kwargs'] = self.url_kwargs(self)
        context['template_engine'] = self.site.template_engine
        context['renderer'] = self.site.renderer

        # Set an external template for the breadcrumbs
        if hasattr(self.site, 'breadcrumb_trail_template'):
            context['breadcrumb_trail_template'] = self.site.breadcrumb_trail_template

        # Get additional context data
        for property in self.site.site_context_fields:
            if hasattr(self, property):
                context[property] = self.__getattribute__(property)

        return context

    def prep_buttons(self, button_dict):
        """ Checks if none of the buttons contains some kind of complex revere functionality that requires
        this class'url kwargs """
        new_dict = {}
        for key, url in button_dict.items():
            if callable(url):
                new_dict[key] = url(self)
            else:
                new_dict[key] = url
        return new_dict

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

        if self.site is not None and self.site.can_be_edited:
            # Create the Edit Page button
            namespace = self.request.resolver_match.namespace
            self.header_buttons['Edit Page'] = reverse(namespace+':edit_page', kwargs=kwargs, current_app=namespace)


class PageEditMixin(LoginRequiredMixin, PageMixin):
    """ A mixin for the page editing back-end """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['overlay'] = self.get_overlay()
        context['spacer'] = self.get_spacer()
        context['active_container'] = self.get_active_container()
        return context

    def get_overlay(self):
        """ Returns the initiated overlay object used in the view """
        try:
            # Enable more flexible mixing ordering by checking the parent
            return super().get_overlay()
        except AttributeError:
            return None

    def get_spacer(self):
        """ Returns the initiated overlay object used in the view """
        try:
            # Enable more flexible mixing ordering by checking the parent
            return super().get_spacer()
        except AttributeError:
            return None

    def get_active_container(self):
        """ Returns the active (selected) container in which work is currently done """
        try:
            # Enable more flexible mixing ordering by checking the parent
            return super().get_active_container()
        except AttributeError:
            return self.page.root_module

    def init_params(self, **kwargs):
        super(PageEditMixin, self).init_params(**kwargs)

        if self.site is not None:
            # Create the View Page button
            self.header_buttons['View Page'] = reverse_ns(self.request, 'view_page', kwargs=self.url_kwargs(self))


class PageAlterView(PageEditMixin, TemplateView):
    """ The root for the page alteration """
    template_name = 'pagedisplay/page_edit_page.html'

    def get_overlay(self):
        return ModuleSelectOverlay()

    def get_context_data(self, **kwargs):
        context = super(PageAlterView, self).get_context_data()

        extra_buttons = copy.deepcopy(self.site.extra_page_options)
        for key, option in extra_buttons.items():
            option.setdefault('button', {})
            option['button'].setdefault('text', key)
            option['button'].setdefault('type', 'btn-primary')

            option.setdefault('text', key)

            # Set the url
            if option.get('form_class', None):
                # Overwrite the present url, there is a site view implemented
                option['button']['url'] = reverse_ns(
                    self.request,
                    'edit_extra_option',
                    kwargs={'extra_slug': key, **self.url_kwargs(self)}
                )
            else:
                # Try to form a url. Likely it is a custom user view with the same input attributes
                try:
                    option['button']['url'] = reverse(
                        option['button'].get('url'),
                        kwargs={**self.url_kwargs(self)}
                    )
                except KeyError:
                    option['button'].setdefault('úrl', '')

        context['extra_buttons'] = [
            *[option['button'] for key, option in extra_buttons.items()]
        ]

        context['can_be_deleted'] = self.site.can_be_deleted

        return context


class PageEditExtraOptionView(PageMixin, FormView):
    template_name = 'pagedisplay/page_edit_other_form.html'

    # The defined extra option containing all data that is relevant for this view
    extra_option = None

    def get_success_url(self):
        if self.extra_option.get('return_on_success', True):
            return reverse_ns(self.request, 'edit_page', kwargs=self.url_kwargs(self))
        else:
            return reverse_ns(self.request, 'edit_extra_option',
                              kwargs={**self.url_kwargs(self), 'extra_slug': self.kwargs['extra_slug']})

    def get_form_kwargs(self):
        kwargs = super(PageEditExtraOptionView, self).get_form_kwargs()
        kwargs.update({
            'page': self.page,
        })
        return kwargs

    def get_form_class(self):
        return self.extra_option['form_class']

    def form_valid(self, form):
        form.save()
        return super(PageEditExtraOptionView, self).form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        # Get the extra options dict or raise 404 if not set-up correctly
        self.extra_option = self.site.extra_page_options.get(kwargs['extra_slug'], None)
        if self.extra_option is None or self.extra_option.get('form_class', None) is None:
            raise Http404()
        return super(PageEditExtraOptionView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(PageEditExtraOptionView, self).get_context_data(**kwargs)
        kwargs.update({
            'extra_option': self.extra_option
        })
        return kwargs


class PageAlterSettingsView(PageEditMixin, UpdateView):
    """ Contains a form for page settings """
    template_name = 'pagedisplay/page_edit_settings.html'

    def get_object(self, queryset=None):
        return self.page

    def get_success_url(self):
        return reverse_ns(self.request, 'edit_page', kwargs=self.url_kwargs(self))

    def get_form_class(self):
        # Set the model fields based on the model
        self.fields = self.page.option_fields
        self.model = self.page.__class__
        # Below the modelform is automatically created
        return super(PageAlterSettingsView, self).get_form_class()


class PageDeleteView(PageMixin, DeleteView):
    template_name = "pagedisplay/page_delete_form.html"

    def get_object(self, queryset=None):
        return self.page

    def get_success_url(self):
        if self.site.delete_success_url:
            if callable(self.site.delete_success_url):
                return self.site.delete_success_url(self.page, **self.kwargs)
            elif isinstance(self.site.delete_success_url, str):
                return self.site.delete_success_url
            else:
                raise AttributeError(
                    f"{self.site.__class__} has an incorrect delete_success_url defined. Make sure it's either "
                    f"a callable with 'page' as input argument and all current url-kwargs as input kwargs "
                    f"or a url string."
                )
        elif self.site.use_overview:
            return reverse_ns(self.request, 'overview', kwargs=self.url_kwargs(self))
        else:
            raise AttributeError(
                f"{self.site.__class__} has no delete_success_url defined. Define this (attribute or method) so "
                f"the site can redirect to the correct page upon page deletion"
            )


# ####################################################
# ############    Page Module Views    ###############
# ####################################################


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

        module_form = None
        # If there are no get parameters, initiate the root_form, otherwise. Get those paramaters and check validity
        if len(self.request.GET) == 0:
            root_form = AddModuleForm(site=self.site)
            position_form = ModuleLinkForm()
        else:
            root_form = AddModuleForm(site=self.site, data=self.request.GET)
            position_form = ModuleLinkForm(data=self.request.GET)

            if root_form.is_valid() and position_form.is_valid():
                # Basic parameters are valid so hide the root_form from now on.
                instance = root_form.get_instance()
                self.position = position_form.cleaned_data['position']
                root_form.make_hidden()
                # Initiate the module form from the root_form instance
                module_form = build_moduleform(instance=instance)

        context = super().get_context_data(**kwargs)
        context['container'] = self.container
        context['module_form'] = module_form
        context['root_form'] = root_form
        context['position_form'] = position_form

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        # Construct the root form
        root_form = AddModuleForm(data=self.request.POST, files=self.request.FILES, site=self.site)
        context['root_form'] = root_form
        position_form = ModuleLinkForm(data=self.request.POST)
        context['position_form'] = position_form

        if root_form.is_valid() and position_form.is_valid():
            # Root form is valid, construct module_form
            instance = root_form.get_instance()
            module_form = build_moduleform(instance=instance, data=request.POST, files=self.request.FILES)

            if module_form.is_valid():
                # Module_form is valid. Save the module and go back to the edit page
                module_form.save()
                self.site.on_module_creation(self.page, module_form.instance)
                position_form.save(module_form.instance)
                return HttpResponseRedirect(reverse_ns(self.request, 'edit_page', kwargs=self.url_kwargs(self)))

            context['module_form'] = module_form

        return self.render_to_response(context)

    def get_spacer(self):
        if len(self.request.GET) > 0:
            if ModuleLinkForm(data=self.request.GET).is_valid():
                return InsertModuleMarkerSpacer(active_container=self.get_active_container(),
                                                position=self.position)
        return InsertModuleSpacer()


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
        return ModuleEditOverlay(selected_module=self.selected_module)

    def get_active_container(self):
        return self.selected_module.container.first()


class ModuleEditBase(ModuleEditMixin, PageEditMixin):
    """ The general overlap for all module edit views """
    pass


class PageAlterModuleView(ModuleEditBase, UpdateView):
    """ Adjust the details of a given module """
    template_name = 'pagedisplay/page_edit_module.html'

    def get_object(self, queryset=None):
        return self.selected_module

    def get_success_url(self):
        return reverse_ns(self.request, 'edit_page', kwargs=self.url_kwargs(self))

    def get_form_class(self):
        return build_moduleform(
            instance=self.selected_module,
            exclude_fields=self.selected_module.exclude_editing_fields,
            get_as_class=True
        )


class PageMoveModuleView(ModuleEditBase, FormView):
    template_name = 'pagedisplay/page_edit_module_move.html'
    form_class = ModuleLinkForm

    def post(self, request, *args, **kwargs):
        return super(PageMoveModuleView, self).post(request,*args, **kwargs)

    def form_valid(self, form):
        form.save(self.selected_module)
        return super(PageMoveModuleView, self).form_valid(form)

    def get_success_url(self):
        url_kwargs = self.url_kwargs(self)
        url_kwargs['module_id'] = self.selected_module.id
        return reverse_ns(self.request, 'edit_page', kwargs=url_kwargs)

    def get_overlay(self):
        return HideModuleOverlay(self.selected_module)

    def get_spacer(self):
        return InsertModuleMoveSpacer(self.selected_module)


class PageDeleteModuleView(ModuleEditBase, DeleteView):
    model = BaseModule
    selected_module = None
    template_name = "pagedisplay/page_edit_module_delete.html"

    def get_object(self, queryset=None):
        return self.selected_module

    def delete(self, *args, **kwargs):
        self.site.on_module_deletion(self.page, self.get_object())
        return super(PageDeleteModuleView, self).delete(*args, **kwargs)

    def get_success_url(self):
        return reverse_ns(self.request, 'edit_page', kwargs=self.url_kwargs(self))
