from django.urls import path, include

from reports import views, views_setup
from reports.sites import report_site

app_name = "reports"

urlpatterns = [
    path('reports/', include([
        path('', views_setup.ReportsOverview.as_view(), name='reports_overview'),
        path('add/', views_setup.AddReportView.as_view(), name='add_report'),
        path('<slug:report_slug>/', include([
            path('', views_setup.ReportInfoView.as_view(), name='details'),
            path('add/', views_setup.AddReportPageView.as_view(), name='add_page'),
            path('<int:report_page_id>/', include([
                path('', views_setup.ReportPageInfoView.as_view(), name='details'),
                path('display/', report_site.urls)
            ]))
        ])),
    ])),
    path('preview/', include([
        path('', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
        path('<int:page_number>/', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
    ])),
    path('plot/', views.ResultsPDFPlotter.as_view(), name='results_pdf'),
]