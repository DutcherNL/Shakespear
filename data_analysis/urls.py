from django.urls import path, include

from . import views, json_charts

from data_analysis import views_analysis

app_name = "data_analysis"

urlpatterns = [
    path('', views.InquiryDataView.as_view(), name='overview'),
    path('technologies/', views.TechDataView.as_view(), name='techs'),
    path('json/', include([
        path('inquiry_creation/', json_charts.InquiryCreationChart.as_view(), name='json_creation'),
        path('inquiry_progress/', json_charts.InquiryProgressChart.as_view(), name='json_progress'),
        path('tech_result/<int:tech_id>/', json_charts.TechProgressChart.as_view(), name='json_techs'),
    ])),
    path('analysis/', include([
        path('', views_analysis.AnalysisListView.as_view(), name='analysis_overview'),
        path('<int:pk>/', include([
            path('', views_analysis.InquiryAnalysis.as_view(), name='analysis_detail'),
            path('activate/', views_analysis.ActivateInquirerView.as_view(), name='analysis_activate'),
            path('mail/', views_analysis.ConstructMailForInquiryView.as_view(), name='analysis_mailing'),
        ])),
    ])),
]