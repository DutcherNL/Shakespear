from django.urls import path

from . import views

urlpatterns = [
    path('<int:inf_id>', views.InfoPageView.as_view(), name='info_page'),
]