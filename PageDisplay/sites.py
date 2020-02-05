from functools import update_wrapper

from django.urls import path, include

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

    @property
    def urls(self):
        return self.get_urls(), 'PageDisplay', self.name

    def get_urls(self):
        """ Returns the urls for the page module """

        # A wrapper to allow class get_view do reverse url functions when setting up a view class
        def wrap(view_class):
            def wrapper(*args, **kwargs):
                return self.get_view(view_class)(*args, **kwargs)
            return update_wrapper(wrapper, view_class)

        urlpatterns = []

        # Whether an overview page of all pages is present
        if self.use_overview:
            urlpatterns += [path('all/', views.PageOverview.as_view(), name='overview')]

        # Whether the page id is determined by itself or something else
        if self.use_page_keys:
            url_string = 'pages/<int:page_id>/'
        else:
            url_string = ''

        urlpatterns += [
            path(url_string, include([
                path('', wrap(views.PageInfoView), name='view_page'),
                path('edit/', include([
                    path('', wrap(views.PageAlterView), name='edit_page'),
                    path('settings/', wrap(views.PageAlterSettingsView), name='edit_page_settings'),
                    path('add/<int:container_id>/', wrap(views.PageAddModuleView), name='edit_page_add'),
                    path('<int:module_id>/', wrap(views.PageAlterModuleView), name='edit_page'),
                    path('del/<int:module_id>/', wrap(views.PageDeleteModuleView), name='edit_page_delete_module')
                ])),
            ])),
        ]

        return urlpatterns

    def get_view(self, view_class):
        """ Returns a customised view """
        inits = self.get_view_init_kwargs(view_class)
        return view_class.as_view(**inits)

    def get_view_init_kwargs(self, view_class):
        return {
            'site': self,
            'extends': self.extends,
            'header_buttons': self.get_header_buttons(view_class),
            'init_view_params': self.init_view_params,
            'url_kwargs': self.get_url_kwargs
        }

    @staticmethod
    def get_url_kwargs(view_obj):
        return {
            'page_id': view_obj.page.id
        }

    def get_header_buttons(self, view_class):
        """ Returns a dictionary of urls to craft buttons that will be displayed in the header in all situations
        Items should be added to the dict in the form: 'button_name': 'button_url'
        e.g. buttons['home'] = 'https://yoursite.url/home/'
        """
        return {}

    def get_availlable_modules(self):
        """ Returns availlable modules """
        return registry.get_all_modules()

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        This methoed can also check access by raising a 404Error or 403Error
        """
        view_obj.page = Page.objects.get(pk=kwargs['page_id'])


page_site = PageSite()
