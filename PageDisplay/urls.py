from django.urls import path, include

from . import views

urlpatterns = [
    path('<int:inf_id>/', include([
        path('',views.InfoPageView.as_view(), name='info_page'),
        path('edit/', include([
            path('', views.PageAlterView.as_view(), name='edit_page'),
            path('<int:module_id>', views.PageAlterModuleView.as_view(), name='edit_page')
            ])),
        ])),
]