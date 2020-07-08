from functools import update_wrapper

from django.urls import path, include
from django.http import HttpResponseForbidden, Http404

from PageDisplay import views
from PageDisplay.module_registry import registry
from PageDisplay.models import Page

__all__ = ['PageSite']


class PageSite:
    """ The PageSite object encapsulates an instance of the PageDisplay application

    A PageSite is the 'admin of Pages'. It allows control of who can edit/view what pages and how they can be edited.

    use_overview: add an overview page at '/all/' in the url
    use_page_keys: adds a page key identifier in the url. Set False if you want to implement your own
    can_be_edited: Whether this site can be used to edit page layouts

    extends_template: adjust the default template it is build upon with your own design
    template_engine: the template engine when rendering the page.
    site_context_fields: a list of argument names that will be copied from the view object into the template context
    """
    namespace = 'pages'

    # Broad controls
    use_overview = False
    use_page_keys = True
    can_be_edited = True

    extends_template = None
    template_engine = None
    site_context_fields = []
    renderer = None

    view_requires_login = True
    edit_requires_login = True
    view_requires_permissions = []
    edit_requires_permissions = []

    # Limit the type  of modules that can be created
    include_modules = None
    exclude_modules = None

    @property
    def urls(self):
        return self.get_urls(), 'PageDisplay', self.namespace

    def get_urls(self):
        """ Returns the urls for the page module """

        # A wrapper to allow class get_view do reverse url functions when setting up a view class
        def wrap(view_class):
            def wrapper(request, *args, **kwargs):
                # Construct the view
                init_values = self.get_view_init_kwargs(view_class)
                return view_class.as_view(**init_values)(request, *args, **kwargs)

            return update_wrapper(wrapper, view_class)

        urlpatterns = []

        # Whether an overview page of all pages is present
        if self.use_overview:
            init_values = {
                'site': self,
            }
            urlpatterns += [path('all/', views.PageOverview.as_view(**init_values), name='overview')]

        # Whether the page id is determined by itself or something else
        if self.use_page_keys:
            url_string = '<int:page_id>/'
        else:
            url_string = ''

        if self.can_be_edited:
            edit_urls = path('edit/', include([
                path('', wrap(views.PageAlterView), name='edit_page'),
                path('settings/', wrap(views.PageAlterSettingsView), name='edit_page_settings'),
                path('add/', wrap(views.PageAddModuleView), name='edit_page_add'),
                path('<int:module_id>/', include([
                    path('', wrap(views.PageAlterModuleView), name='edit_page'),
                    path('move/', wrap(views.PageMoveModuleView), name='edit_page_move_module'),
                    path('delete/', wrap(views.PageDeleteModuleView), name='edit_page_delete_module'),
                ])),
            ]))

            urlpatterns += [
                path(url_string, include([
                    path('', wrap(views.PageInfoView), name='view_page'),
                    edit_urls
                ])),
            ]
        else:
            urlpatterns += [
                path(url_string, include([
                    path('', wrap(views.PageInfoView), name='view_page')
                ]
                )),
            ]

        return urlpatterns

    def get_view_init_kwargs(self, view_class):
        """ Builds a list of initial key_word arguments"""
        return {
            'site': self,
            'extends': self.extends_template,
            'header_buttons': self.get_header_buttons(view_class),
            'init_view_params': self.init_view_params,
            'url_kwargs': self.get_url_kwargs
        }

    def can_access(self, request, view_obj):
        """
        Checks whether the current requeset is valid. Allows checking for logged_in, permissions etc.
        Returns False if access is forbidden.
        This method is called in the View dispatch method. It returns an If statement for convience in returning
        ResponseForbiddenRequests (which opposed to 404 errors are not an Error that can be raised)
        """
        if isinstance(view_obj, views.PageInfoView):
            # Check user logged in requirement
            if not request.user.is_authenticated and self.view_requires_login:
                return False
            # Check all persmissions
            for permission in self.view_requires_permissions:
                if not request.user.has_perm(permission):
                    return False
        elif isinstance(view_obj, views.PageOverview):
            if not request.user.is_authenticated and self.view_requires_login:
                return False
            for permission in self.view_requires_permissions:
                if not request.user.has_perm(permission):
                    return False
        else:
            # It is one of the Editing views by exclusion
            if not request.user.is_authenticated and self.edit_requires_login:
                raise False
            # Check all persmissions
            for permission in self.edit_requires_permissions:
                if not request.user.has_perm(permission):
                    raise False
        return True

    @staticmethod
    def get_url_kwargs(view_obj):
        """ A method that extracts all the required url arguments from the view object 'view_obj'.
        Replace this method to insert your own unique url tracing. For instance when you want to obtain the
        page object through a different object:
        class SpecialBlogPost:
            page = models.ForeignKey(Page)

        get_url_kwargs(view_obj):
            return {'blog_id': view_obj.blog}
        """
        if view_obj.site.use_page_keys:
            return {
                'page_id': view_obj.page.id
            }
        else:
            return {}

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        To check access, use an extention of the can_access method

        Use this when for instance you want to obtain the page object through a diffent object:
        class SpecialBlogPost:
            page = models.ForeignKey(Page)

        init_view_params(view_obj):
            view_obj.blog_id = SpecialBlogPost.objects.get(pk=kwargs['blog_id'])
            view_obj.page = blog_id.page # set the page parameter
        """
        if view_obj.site.use_page_keys:
            page = view_obj.site.get_queryset().filter(pk=kwargs['page_id']).first()
            # Make sure it is the right sub-class (if applicable)
            if page:
                view_obj.page = page.get_as_child()
            else:
                if isinstance(view_obj, views.PageOverview):
                    pass
                else:
                    raise Http404

    def get_header_buttons(self, view_class):
        """ Returns a dictionary of urls to craft buttons that will be displayed in the header in all situations
        Items should be added to the dict in the form: 'button_name': 'button_url'
        e.g. buttons['home'] = 'https://yoursite.url/home/'
        """
        return {}

    def get_availlable_modules(self):
        """ Returns availlable modules """
        if self.include_modules and self.exclude_modules:
            raise AssertionError("get_module_list in module registry can not have both an include and exclude list")

        return registry.get_module_list(include=self.include_modules,
                                        exclude=self.exclude_modules)

    def get_queryset(self):
        """ Returns the queryset of availlable page objects.
        In order to limit the possible Page objects to your liking overwrite this method.
        Note: This method only applies when use_page_keys is set to True or when use_overview is True
        """
        return Page.objects.all()

    def on_module_creation(self, page, module):
        """ Method called when a module is created. Can be useful for triggering other events """
        pass

    def on_module_deletion(self, page, module):
        """ Method called when a module is deleted. Can be useful for triggering other events """
        pass


page_site = PageSite()
