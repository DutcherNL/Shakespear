from functools import update_wrapper

from django.urls import path, include
from django.http import HttpResponseForbidden

from PageDisplay import views
from PageDisplay.module_registry import registry
from PageDisplay.models import Page


__all__ = ['PageSite']


class PageSite:
    """
    The PageSite object encapsulates an instance of the PageDisplay application
    """
    name = 'pages'
    extends = None
    use_overview = True
    use_page_keys = True
    template_engine = None
    site_context_fields = []

    view_requires_login = True
    edit_requires_login = True
    view_requires_permissions = []
    edit_requires_permissions = []

    @property
    def urls(self):
        return self.get_urls(), 'PageDisplay', self.name

    def get_urls(self):
        """ Returns the urls for the page module """

        # A wrapper to allow class get_view do reverse url functions when setting up a view class
        def wrap(view_class):
            def wrapper(request, *args, **kwargs):
                # Block access if it needs to be blocked
                if not self.can_access(request, view_class):
                    return HttpResponseForbidden("You are not allowed to access this page")

                # Construct the view
                init_values = self.get_view_init_kwargs(view_class)
                return view_class.as_view(**init_values)(request, *args, **kwargs)
            return update_wrapper(wrapper, view_class)

        urlpatterns = []

        # Whether an overview page of all pages is present
        if self.use_overview:
            urlpatterns += [path('all/', views.PageOverview.as_view(), name='overview')]

        # Whether the page id is determined by itself or something else
        if self.use_page_keys:
            url_string = '<int:page_id>/'
        else:
            url_string = ''

        urlpatterns += [
            path(url_string, include([
                path('', wrap(views.PageInfoView), name='view_page'),
                path('edit/', include([
                    path('', wrap(views.PageAlterView), name='edit_page'),
                    path('settings/', wrap(views.PageAlterSettingsView), name='edit_page_settings'),
                    path('add/<int:container_id>/', wrap(views.PageAddModuleView), name='edit_page_add'),
                    path('<int:module_id>/', include([
                        path('', wrap(views.PageAlterModuleView), name='edit_page'),
                        path('move/', wrap(views.PageMoveModuleView), name='edit_page_move_module'),
                        path('delete/', wrap(views.PageDeleteModuleView), name='edit_page_delete_module'),
                    ])),
                ])),
            ])),
        ]

        return urlpatterns

    def get_view_init_kwargs(self, view_class):
        return {
            'site': self,
            'extends': self.extends,
            'header_buttons': self.get_header_buttons(view_class),
            'init_view_params': self.init_view_params,
            'url_kwargs': self.get_url_kwargs
        }

    def can_access(self, request, view_class):
        """
        Checks whether the current requeset is valid. Allows checking for logged_in, permissions etc
        :param view_obj:
        :param request:
        :return:
        """
        if view_class is views.PageInfoView:
            # Check user logged in requirement
            if not request.user.is_authenticated and self.view_requires_login:
                return False
            # Check all persmissions
            for permission in self.view_requires_permissions:
                if not request.user.has_perm(permission):
                    return False
        else:
            if not request.user.is_authenticated and self.edit_requires_login:
                return False
            # Check all persmissions
            for permission in self.edit_requires_permissions:
                if not request.user.has_perm(permission):
                    return False

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
        return {
            'page_id': view_obj.page.id
        }

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        This methoed can also check access by raising a 404Error or 403Error

        Use this when for instance you want to obtain the page object through a diffent object:
        class SpecialBlogPost:
            page = models.ForeignKey(Page)

        init_view_params(view_obj):
            view_obj.blog_id = SpecialBlogPost.objects.get(pk=kwargs['blog_id'])
            view_obj.page = blog_id.page # set the page parameter
        """
        view_obj.page = Page.objects.get(pk=kwargs['page_id']).get_as_child()

    def get_header_buttons(self, view_class):
        """ Returns a dictionary of urls to craft buttons that will be displayed in the header in all situations
        Items should be added to the dict in the form: 'button_name': 'button_url'
        e.g. buttons['home'] = 'https://yoursite.url/home/'
        """
        return {}

    def get_availlable_modules(self):
        """ Returns availlable modules """
        return registry.get_all_modules()


page_site = PageSite()
