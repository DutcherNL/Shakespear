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
            path('add/', views_setup.CreateReportPageView.as_view(), name='add_page'),
            path('edit/', include([
                path('options/', views_setup.ReportUpdateView.as_view(), name='edit_report'),
                path('display/', views_setup.ReportDisplayOptionsUpdateView.as_view(), name='edit_display'),
            ])),
            path('pdf/', views_setup.PrintReportAsPDFView.as_view(), name='pdf'),
            path('pdf_preview/', views_setup.PrintReportAsHTMLView.as_view(), name='pdf_preview'),
            path('<int:report_page_id>/', include([
                path('', views_setup.ReportPageInfoView.as_view(), name='details'),
                path('edit/', views_setup.ReportPageUpdateView.as_view(), name='edit_page'),
                path('pdf/', views_setup.PrintPageAsPDFView.as_view(), name='pdf'),
                path('pdf_preview/', views_setup.PrintPageAsHTMLView.as_view(), name='pdf_preview'),
                path('display/', report_site.urls)
            ])),
        ])),
    ])),
    path('preview/', include([
        path('', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
        path('<int:page_number>/', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
    ])),
    path('plot/', views.ResultsPDFPlotter.as_view(), name='results_pdf'),
]