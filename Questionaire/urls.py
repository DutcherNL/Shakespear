from django.urls import path

from . import views, views_debug

urlpatterns = [
    path('', views_debug.StartViewDebug.as_view(), name='home'),
    path('debug_overview', views_debug.QueryIndexViewDebug.as_view(), name='debug_inquiries_overview'),
    path('debug_new/', views_debug.CreateNewInquiryViewDebug.as_view(), name='debug_new_query'),
    path('debug_start/<int:inquiry>', views_debug.InquiryStartScreenDebug.as_view(), name='debug_start_query'),
    path('debug_inq/<int:inquiry>/<int:page>/', views_debug.QPageViewDebug.as_view(), name='debug_q_page'),
    path('debug_inq/<int:inquiry>/progress/', views_debug.InquiryScoresViewDebug.as_view(), name='debug_inq_scores'),

    path('main/', views.QuesetionHomeScreenView.as_view(), name='index_screen'),
    path('inquriy/new/', views.CreateNewInquiryView.as_view(), name='new_query'),
    path('inquiry/welcome', views.InquiryStartScreen.as_view(), name='start_query'),
    path('inquiry/run/', views.QPageView.as_view(), name='run_query'),
    path('inquiry/continue/', views.UserConfirmationPage.as_view(), name='run_continue'),
]