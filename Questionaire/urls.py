from django.urls import path

from . import views

urlpatterns = [
    path('', views.QueryIndexView.as_view(), name='inquiries_overview'),
    path('new/', views.CreateNewInquiryView.as_view(), name='new_query'),
    path('start/<int:inquiry>', views.InquiryStartScreen.as_view(), name='start_query'),
    path('<int:inquiry>/<int:page>/', views.QPageView.as_view(), name='q_page'),
    path('<int:inquiry>/progress/', views.InquiryScoresView.as_view(), name='inq_scores'),
]