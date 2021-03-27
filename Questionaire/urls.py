from django.urls import path, include

from . import views, views_analysis

urlpatterns = [
    path('main/', views.QuesetionHomeScreenView.as_view(), name='index_screen'),
    path('jump_to_current_place/', views.JumpToCurrentView.as_view(), name='jump_to_current'),

    path('inquiry/', include([
        path('new/', views.CreateNewInquirerView.as_view(), name='new_query'),
        path('welcome', views.InquiryStartScreen.as_view(), name='start_query'),
        path('run/', views.QPageView.as_view(), name='run_query'),
        path('login/', views.LogInInquiry.as_view()),
        path('get_query/', views.GetInquirerView.as_view(), name='run_continue'),
        path('continue/', views.InquiryContinueScreen.as_view(), name='continue_query'),
        path('reset_query/', views.ResetQueryView.as_view(), name='reset_inquiry'),

        path('results/', include([
            path('', views.QuestionaireCompleteView.as_view(), name='results_display'),
            path('advised/', views.QuestionaireAdvisedView.as_view(), name='results_advised'),
            path('not-advised/', views.QuestionaireRejectedView.as_view(), name='results_not_advised'),
            path('pdf/', include('reports.urls')),
        ])),
    ])),
    path('analysis/', include([
        path('', views_analysis.AnalysisListView.as_view(), name='analysis_overview'),
        path('<int:pk>/', include([
            path('', views_analysis.InquiryAnalysis.as_view(), name='analysis_detail'),
            path('mail/', views_analysis.ConstructMailForInquiryView.as_view(), name='analysis_mailing'),
        ])),
    ])),
]