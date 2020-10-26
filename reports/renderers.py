from PageDisplay.renderers import BasePageRenderer
from reports.modules.widgets import TechScorePDFWidget, ImagePDFWidget, TechScorePreviewPDFWidget
from django.conf import settings


class ReportPageRenderer(BasePageRenderer):
    template_name = "reports/page_display/papersize_container.html"

    replaced_module_widgets = [
        ('TechScoreModule', TechScorePreviewPDFWidget)
    ]

    def get_context_data(self, **kwargs):
        context = super(ReportPageRenderer, self).get_context_data(**kwargs)
        report_display_options = self.page.reportpagelink.report.display_options

        if self.page.layout:
            margins = self.page.layout.margins
        else:
            margins = report_display_options.margins

        context['measurements'] = {
            'margins': margins,
            'size': report_display_options.paper_proportions
        }

        context['layout_context'] = self.get_layout_context(**kwargs)

        return context

    def get_layout_context(self, **kwargs):
        return {
            'header': self.page.reportpagelink.report.display_options.header,
            'footer': self.page.reportpagelink.report.display_options.footer,
            'p_num': kwargs.get('p_num', 1)
        }


class ReportPagePDFRenderer(ReportPageRenderer):
    replaced_module_widgets = [
        ('ImageModule', ImagePDFWidget),
        ('TechScoreModule', TechScorePDFWidget),
    ]
