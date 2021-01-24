from django.urls import path, include, reverse

from .page_site import tech_page_site, inquiry_pages_site
from . import views
from shakespeare_setup.config import SetupConfig


class SetupTechs(SetupConfig):
    name = "Technologies"
    url_keyword = 'techs'
    namespace = 'technologies'

    def get_urls(self):
        """ Builds a list of urls """
        return [
            path('', views.SetUpTechPageOverview.as_view(), name='home'),
            path('<int:tech_id>/', include([
                path('settings/', views.UpdateTechnologyView.as_view(), name='tech_update'),
                path('create_page/', views.CreateTechPageView.as_view(), name='create_page'),
                path('page/', tech_page_site.urls)
            ])),
        ]


class SetupInquiryPages(SetupConfig):
    name = "Inquiry Pages"
    url_keyword = 'inquiry_pages'
    namespace = 'questionaire_pages'

    def get_urls(self):
        """ Builds a list of urls """
        return [
            path('', views.SetUpQuestionairePageOverview.as_view(), name='home'),
            path('<int:page_id>/', include([
                path('create_display_page/', views.CreateQuestionaireDisplayPageView.as_view(), name='create_display_page'),
                path('display/', inquiry_pages_site.urls)
            ])),
        ]
