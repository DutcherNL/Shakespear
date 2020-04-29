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
        report_display_options = self.page.report.display_options

        context['measurements'] = {
            'margins': report_display_options.margins,
            'size': report_display_options.paper_proportions
        }
        context['font_size_correction'] = settings.PDF_BASE_FONT_SIZE

        if self.page.has_header_footer:
            context['header'] = report_display_options.header
            context['footer'] = report_display_options.footer
        return context


class ReportPagePDFRenderer(ReportPageRenderer):
    replaced_module_widgets = [
        ('ImageModule', ImagePDFWidget),
        ('TechScoreModule', TechScorePDFWidget),
    ]
