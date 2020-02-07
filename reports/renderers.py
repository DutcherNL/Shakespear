from PageDisplay.renderers import BasePageRenderer


class ReportPageRenderer(BasePageRenderer):
    template_name = "reports/page_display/papersize_container.html"

    def get_context_data(self, **kwargs):
        context = super(ReportPageRenderer, self).get_context_data(**kwargs)
        context['measurements'] = {
            'margins': "20mm 20mm 20mm 20mm",
            'size': self.paper_proportions
        }
        return context

    @property
    def paper_proportions(self):
        """ Returns a dict of the height and width of the pgae"""
        return {'width': "210mm", 'height':"297mm"}
        #Todo

        if self.page.size == 'A3':
            size = ("297mm", "420mm")
        if self.page.size == 'A4':
            sizes = ("210mm", "297mm")
        if self.page.size == 'A5':
            sizes = ("148mm", "210mm")

        if self.orientation:
            return {'width': sizes[0], 'height': sizes[1]}
        return {'width': sizes[1], 'height': sizes[0]}


