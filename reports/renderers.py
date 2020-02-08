from PageDisplay.renderers import BasePageRenderer


class ReportPageRenderer(BasePageRenderer):
    template_name = "reports/page_display/papersize_container.html"

    def get_context_data(self, **kwargs):
        context = super(ReportPageRenderer, self).get_context_data(**kwargs)
        report_display_options = self.page.report.display_options

        context['measurements'] = {
            'margins': report_display_options.margins,
            'size': report_display_options.paper_proportions
        }
        if self.page.has_header_footer:
            context['header'] = report_display_options.header
            context['footer'] = report_display_options.footer
        return context


