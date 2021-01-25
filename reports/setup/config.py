from django.urls import path, include


from shakespeare_setup.config import SetupConfig
from . import views
from .sites import report_site


class SetupTechs(SetupConfig):
    name = "Reports"
    url_keyword = 'reports'
    namespace = 'reports'
    root_url_name = 'reports_overview'

    def get_urls(self):
        """ Builds a list of urls """
        return [
            path('reports/', include([
                path('', views.ReportsOverview.as_view(), name='reports_overview'),
                path('add/', views.AddReportView.as_view(), name='add_report'),
                path('<slug:report_slug>/', include([
                    path('', views.ReportInfoView.as_view(), name='details'),
                    path('edit/', include([
                        path('options/', views.ReportUpdateView.as_view(), name='edit_report'),
                        path('display/', views.ReportDisplayOptionsUpdateView.as_view(), name='edit_display'),
                    ])),
                    path('pdf/', views.PrintReportAsPDFView.as_view(), name='pdf'),
                    path('pdf_preview/', views.PrintReportAsHTMLView.as_view(), name='pdf_preview'),
                    path('layout/', include([
                        path('', views.ReportLayoutListView.as_view(), name='layout_overview'),
                        path('add/', views.ReportAddLayoutView.as_view(), name='add_layout'),
                        path('<layout:layout>/', include([
                            path('layout/', views.ReportChangeLayoutView.as_view(), name='edit_layout'),
                            path('edit/', views.ReportChangeLayoutSettingsView.as_view(), name='edit_layout_settings'),
                        ])),
                    ])),

                    path('page/', include([
                        path('add/', views.CreateReportPageView.as_view(), name='add_page'),
                        path('add_multi/', views.CreateReportMultiPageView.as_view(), name='add_multi_page'),
                        path('move_order/', views.ReportMovePageView.as_view(), name='move_page'),
                        path('<int:report_page_id>/', include([
                            path('', views.ReportPageInfoView.as_view(), name='details'),
                            path('edit/', views.ReportPageUpdateView.as_view(), name='edit_page'),
                            path('pdf/', views.PrintPageAsPDFView.as_view(), name='pdf'),
                            path('pdf_preview/', views.PrintPageAsHTMLView.as_view(), name='pdf_preview'),
                            path('display/', report_site.urls),
                            path('conditions/', include([
                                path('', views.ReportPageCriteriaOverview.as_view(), name='page_criterias'),
                                path('create/', views.CreateTechCriteriaView.as_view(), name='add_page_criteria'),
                                path('<int:criteria_id>/', include([
                                    path('edit/', views.EditCriteriaView.as_view(), name='edit_page_criteria'),
                                    path('delete/', views.DeleteCriteriaView.as_view(), name='delete_page_criteria'),
                                ]))
                            ])),
                        ])),
                    ])),
                ])),
            ])),

            # # Todo: Check if the following 3 urls are actually used, does not seem to be the case.
            # path('preview/', include([
            #     path('', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
            #     path('<int:page_number>/', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
            # ])),
            # path('plot/', views.ResultsPDFPlotter.as_view(), name='results_pdf'),
        ]
