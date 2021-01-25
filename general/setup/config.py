from django.urls import path, include


from shakespeare_setup.config import SetupConfig
from .views import *
from .page_site import general_page_site


class SetupTechs(SetupConfig):
    name = "General site pages"
    url_keyword = 'general'
    namespace = 'general'
    root_url_name = 'list'

    button = {
        'image': "img/general/setup/gen-pages-icon.png"
    }

    def get_urls(self):
        """ Builds a list of urls """
        return [
                path('', GeneralPageListView.as_view(), name='list'),
                path('add/', AddGeneralPageView.as_view(), name='add'),
                path('<slug:slug>/', include([
                    path('edit/', UpdateGeneralPageView.as_view(), name='edit'),
                    path('delete/', DeleteGeneralPageView.as_view(), name='delete'),
                    path('page/', general_page_site.urls),
                ])),
        ]