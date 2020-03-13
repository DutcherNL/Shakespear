from django.urls import path, include

from .page_site import page_site
from . import views

app_name = 'setup'

urlpatterns = [
    path('', views.SetUpOverview.as_view(), name='home'),
    path('techs/', include([
        path('', views.SetUpTechPageOverview.as_view(), name='tech_list'),
        path('<int:tech_id>/', include([
            path('settings/', views.UpdateTechnologyView.as_view(), name='tech_update'),
            path('create_page/', views.CreateTechPageView.as_view(), name='create_page'),
            path('page/', page_site.urls)
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
]