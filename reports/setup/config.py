from django.urls import path, include


from shakespeare_setup.config import SetupConfig
from . import views
from .sites import report_site


class SetupTechs(SetupConfig):
    name = "Reports"
    url_keyword = 'reports'
    namespace = 'reports'
    root_url_name = 'reports_overview'
    access_required_permissions = ['reports.change_report']

    button = {
        'image': 'img/reports/setup/report-icon.svg'
    }

    def get_urls(self):
        """ Builds a list of urls """
        wrap = self.limit_access
        return [
            path('reports/', include([
                path('', wrap(views.ReportsOverview.as_view()), name='reports_overview'),
                path('add/', wrap(views.AddReportView.as_view()), name='add_report'),
                path('<slug:report_slug>/', include([
                    path('', wrap(views.ReportInfoView.as_view()), name='details'),
                    path('edit/', include([
                        path('options/', wrap(views.ReportUpdateView.as_view()), name='edit_report'),
                        path('display/', wrap(views.ReportDisplayOptionsUpdateView.as_view()), name='edit_display'),
                    ])),
                    path('pdf/', wrap(views.PrintReportAsPDFView.as_view()), name='pdf'),
                    path('pdf_preview/', wrap(views.PrintReportAsHTMLView.as_view()), name='pdf_preview'),
                    path('layout/', include([
                        path('', wrap(views.ReportLayoutListView.as_view()), name='layout_overview'),
                        path('add/', wrap(views.ReportAddLayoutView.as_view()), name='add_layout'),
                        path('<layout:layout>/', include([
                            path('layout/', wrap(views.ReportChangeLayoutView.as_view()), name='edit_layout'),
                            path('edit/', wrap(views.ReportChangeLayoutSettingsView.as_view()), name='edit_layout_settings'),
                        ])),
                    ])),

                    path('page/', include([
                        path('add/', wrap(views.CreateReportPageView.as_view()), name='add_page'),
                        path('add_multi/', wrap(views.CreateReportMultiPageView.as_view()), name='add_multi_page'),
                        path('move_order/', wrap(views.ReportMovePageView.as_view()), name='move_page'),
                        path('<int:report_page_id>/', include([
                            path('', wrap(views.ReportPageInfoView.as_view()), name='details'),
                            path('edit/', wrap(views.ReportPageUpdateView.as_view()), name='edit_page'),
                            path('pdf/', wrap(views.PrintPageAsPDFView.as_view()), name='pdf'),
                            path('pdf_preview/', wrap(views.PrintPageAsHTMLView.as_view()), name='pdf_preview'),
                            path('display/', report_site.urls),
                            path('conditions/', include([
                                path('', wrap(views.ReportPageCriteriaOverview.as_view()), name='page_criterias'),
                                path('create/', wrap(views.CreateTechCriteriaView.as_view()), name='add_page_criteria'),
                                path('<int:criteria_id>/', include([
                                    path('edit/', wrap(views.EditCriteriaView.as_view()), name='edit_page_criteria'),
                                    path('delete/', wrap(views.DeleteCriteriaView.as_view()), name='delete_page_criteria'),
                                ]))
                            ])),
                        ])),
                    ])),
                ])),
            ])),
        ]
