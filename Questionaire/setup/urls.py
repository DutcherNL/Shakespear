from django.urls import path, include

from .page_site import tech_page_site, inquiry_pages_site
from . import views

app_name = 'setup'

urlpatterns = [
    path('', views.SetUpOverview.as_view(), name='home'),
    path('techs/', include([
        path('', views.SetUpTechPageOverview.as_view(), name='tech_list'),
        path('<int:tech_id>/', include([
            path('settings/', views.UpdateTechnologyView.as_view(), name='tech_update'),
            path('create_page/', views.CreateTechPageView.as_view(), name='create_page'),
            path('page/', tech_page_site.urls)
        ])),
    ])),
    path('inquiry_pages/', include([
        path('', views.SetUpQuestionairePageOverview.as_view(), name='inquiry_list'),
        path('<int:page_id>/', include([
            path('create_display_page/', views.CreateQuestionaireDisplayPageView.as_view(), name='create_display_page'),
            path('display/', inquiry_pages_site.urls)
        ])),
    ])),
    path('reports/', include('reports.urls')),
    path('general/', include([
        path('', views.GeneralPageListView.as_view(), name='general_pages_list'),
        path('add/', views.AddGeneralPageView.as_view(), name='general_page_add'),
        path('<slug:slug>/', include([
            path('edit/', views.UpdateGeneralPageView.as_view(), name='general_page_edit'),
            path('delete/', views.DeleteGeneralPageView.as_view(), name='general_page_delete'),
        ])),
    ])),
    path('mailings/', include('questionaire_mailing.urls')),
    path('data_storage/', include('local_data_storage.urls')),
    path('queued_tasks/', include('queued_tasks.urls')),

]