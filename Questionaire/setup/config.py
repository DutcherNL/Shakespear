from django.urls import path, include, reverse

from .page_site import tech_page_site, inquiry_pages_site
from . import views
from shakespeare_setup.config import SetupConfig


class SetupTechs(SetupConfig):
    name = "Technologies"
    url_keyword = 'techs'
    namespace = 'technologies'
    access_required_permissions = ['Questionaire.change_technology']

    button = {
        'image': 'img/questionaire/setup/atom-icon.svg',
    }

    def get_urls(self):
        """ Builds a list of urls """
        wrap = self.limit_access
        return [
            path('', wrap(views.SetUpTechPageOverview.as_view()), name='home'),
            path('<int:tech_id>/', include([
                path('settings/', wrap(views.UpdateTechnologyView.as_view()), name='tech_update'),
                path('create_page/', wrap(views.CreateTechPageView.as_view()), name='create_page'),
                path('page/', tech_page_site.urls)
            ])),
        ]


class SetupInquiryPages(SetupConfig):
    name = "Inquiry Pages"
    url_keyword = 'inquiry_pages'
    namespace = 'questionaire_pages'
    access_required_permissions = ['Questionaire.change_page']

    button = {
        'image': 'img/questionaire/setup/tablet-icon.svg',
    }

    def get_urls(self):
        """ Builds a list of urls """
        wrap = self.limit_access
        return [
            path('', wrap(views.SetUpQuestionairePageOverview.as_view()), name='home'),
            path('<int:page_id>/', include([
                path('create_display_page/', wrap(views.CreateQuestionaireDisplayPageView.as_view()), name='create_display_page'),
                path('display/', inquiry_pages_site.urls)
            ])),
        ]
