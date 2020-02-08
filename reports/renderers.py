from PageDisplay.renderers import BasePageRenderer


class ReportPageRenderer(BasePageRenderer):
    template_name = "reports/page_display/papersize_container.html"

    def get_context_data(self, **kwargs):
        context = super(ReportPageRenderer, self).get_context_data(**kwargs)
        context['measurements'] = {
            'margins': self.page.report.display_options.margins,
            'size': self.page.report.display_options.paper_proportions
        }
        print(f'CONTEXT {context}')
        return context


