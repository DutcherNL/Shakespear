from django.urls import path, include


from shakespeare_setup.config import SetupConfig
from .views import *
from .page_site import general_page_site


class SetupTechs(SetupConfig):
    name = "General site pages"
    url_keyword = 'general'
    namespace = 'general'
    root_url_name = 'list'
    access_required_permissions = ['general.change_basepageurl']

    button = {
        'image': "img/general/setup/gen-pages-icon.png"
    }

    def get_urls(self):
        """ Builds a list of urls """
        wrap = self.limit_access
        return [
                path('', wrap(GeneralPageListView.as_view()), name='list'),
                path('add/', wrap(AddGeneralPageView.as_view()), name='add'),
                path('<slug:slug>/', include([
                    path('edit/', wrap(UpdateGeneralPageView.as_view()), name='edit'),
                    path('delete/', wrap(DeleteGeneralPageView.as_view()), name='delete'),
                    path('page/', general_page_site.urls),
                ])),
        ]