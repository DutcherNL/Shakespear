from django.urls import path, include


from shakespeare_setup.config import SetupConfig
from .views import *


class SetupTechs(SetupConfig):
    name = "General site pages"
    url_keyword = 'general'
    namespace = None

    def get_urls(self):
        """ Builds a list of urls """
        return [
                path('', GeneralPageListView.as_view(), name='general_pages_list'),
                path('add/', AddGeneralPageView.as_view(), name='general_page_add'),
                path('<slug:slug>/', include([
                    path('edit/', UpdateGeneralPageView.as_view(), name='general_page_edit'),
                    path('delete/', DeleteGeneralPageView.as_view(), name='general_page_delete'),
                ])),
        ]