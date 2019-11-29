from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.PageOverview.as_view(), name='page_overview'),
    path('<int:inf_id>/', include([
        path('',views.InfoPageView.as_view(), name='info_page'),
        path('edit/', include([
            path('', views.PageAlterView.as_view(), name='edit_page'),
            path('settings/', views.PageAlterSettingsView.as_view(), name='edit_page_settings'),
            path('add/<int:container_id>/', views.PageAddModuleView.as_view(), name='edit_page_add'),
            path('<int:module_id>/', views.PageAlterModuleView.as_view(), name='edit_page'),
            path('del/<int:module_id>/', views.PageDeleteModuleView.as_view(), name='edit_page_delete_module')
            ])),
        ])),
]