from django.urls import path, include

from .page_site import page_site
from . import views

app_name = 'setup'

urlpatterns = [
    path('', views.SetUpOverview.as_view(), name='home'),
    path('techs/', include([
        path('', views.SetUpTechPageOverview.as_view(), name='tech_list'),
        path('<int:tech_id>/', include([
            path('edit/', views.RedirectTest.as_view(), name='edit_test'),
            path('settings/', views.UpdateTechnologyView.as_view(), name='tech_update'),
            path('create_page/', views.CreateTechPageView.as_view(), name='create_page'),
            path('page/', page_site.urls)
        ])),
    ])),
]