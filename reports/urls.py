from django.urls import path, include, register_converter

from reports import views, views_setup
from reports.sites import report_site
from reports.url_converters import PageLayoutConverter



register_converter(PageLayoutConverter, 'layout')

app_name = "reports"

urlpatterns = [
    path('reports/', include([
        path('', views_setup.ReportsOverview.as_view(), name='reports_overview'),
        path('add/', views_setup.AddReportView.as_view(), name='add_report'),
        path('<slug:report_slug>/', include([
            path('', views_setup.ReportInfoView.as_view(), name='details'),
            path('edit/', include([
                path('options/', views_setup.ReportUpdateView.as_view(), name='edit_report'),
                path('display/', views_setup.ReportDisplayOptionsUpdateView.as_view(), name='edit_display'),
            ])),
            path('pdf/', views_setup.PrintReportAsPDFView.as_view(), name='pdf'),
            path('pdf_preview/', views_setup.PrintReportAsHTMLView.as_view(), name='pdf_preview'),
            path('layout/', include([
                path('', views_setup.ReportLayoutListView.as_view(), name='layout_overview'),
                path('add/', views_setup.ReportAddLayoutView.as_view(), name='add_layout'),
                path('<layout:layout>/', include([
                    path('layout/', views_setup.ReportChangeLayoutView.as_view(), name='edit_layout'),
                    path('edit/', views_setup.ReportChangeLayoutSettingsView.as_view(), name='edit_layout_settings'),
                ])),
            ])),

            path('page/', include([
                path('add/', views_setup.CreateReportPageView.as_view(), name='add_page'),
                path('add_multi/', views_setup.CreateReportMultiPageView.as_view(), name='add_multi_page'),
                path('move_order/', views_setup.ReportMovePageView.as_view(), name='move_page'),
                path('<int:report_page_id>/', include([
                    path('', views_setup.ReportPageInfoView.as_view(), name='details'),
                    path('edit/', views_setup.ReportPageUpdateView.as_view(), name='edit_page'),
                    path('pdf/', views_setup.PrintPageAsPDFView.as_view(), name='pdf'),
                    path('pdf_preview/', views_setup.PrintPageAsHTMLView.as_view(), name='pdf_preview'),
                    path('display/', report_site.urls),
                    path('conditions/', include([
                        path('', views_setup.ReportPageCriteriaOverview.as_view(), name='page_criterias'),
                        path('create/', views_setup.CreateTechCriteriaView.as_view(), name='add_page_criteria'),
                        path('<int:criteria_id>/', include([
                            path('edit/', views_setup.EditCriteriaView.as_view(), name='edit_page_criteria'),
                            path('delete/', views_setup.DeleteCriteriaView.as_view(), name='delete_page_criteria'),
                        ]))
                    ])),
                ])),
            ])),
        ])),
    ])),
    path('preview/', include([
        path('', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
        path('<int:page_number>/', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
    ])),
    path('plot/', views.ResultsPDFPlotter.as_view(), name='results_pdf'),
]