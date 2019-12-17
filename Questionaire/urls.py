from django.urls import path, include

from reports.views import ResultsPDFPlotter, QuestionaireCompletePDFView

from . import views, views_debug, views_analysis

urlpatterns = [
    path('', views_debug.StartViewDebug.as_view(), name='home'),
    path('debug_overview', views_debug.QueryIndexViewDebug.as_view(), name='debug_inquiries_overview'),
    path('debug_new/', views_debug.CreateNewInquiryViewDebug.as_view(), name='debug_new_query'),
    path('debug_start/<int:inquirer>', views_debug.InquiryStartScreenDebug.as_view(), name='debug_start_query'),
    path('debug_inq/<int:inquiry>/<int:page>/', views_debug.QPageViewDebug.as_view(), name='debug_q_page'),
    path('debug_inq/<int:inquiry>/progress/', views_debug.InquiryScoresViewDebug.as_view(), name='debug_inq_scores'),

    path('main/', views.QuesetionHomeScreenView.as_view(), name='index_screen'),
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