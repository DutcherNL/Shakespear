from django.urls import path

from . import views

urlpatterns = [
    path('<int:page>/', views.QPageView.as_view(), name='q_page'),
]