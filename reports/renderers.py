from PageDisplay.renderers import BasePageRenderer
from reports.modules.widgets import *


from reports.utils import TechListReportPageRetrieval
from Questionaire.utils import get_inquiry_from_request


__all__ = ['ReportSinglePageRenderer', 'ReportSinglePagePDFRenderer', 'ReportMultiPageRenderer', 'ReportMultiPagePDFRenderer']


class ReportRenderingMixin:
    """ Mixin that readies default data when rendering any report page """

    def get_context_data(self, **kwargs):
        context = super(ReportRenderingMixin, self).get_context_data(**kwargs)
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


class ReportSinglePageRenderer(ReportRenderingMixin, BasePageRenderer):
    template_name = "reports/page_display/papersize_container.html"

    replaced_module_widgets = [
        ('TechScoreModule', TechScorePreviewPDFWidget)
    ]


class ReportSinglePagePDFRenderer(ReportSinglePageRenderer):
    replaced_module_widgets = [
        ('ImageModule', ImagePDFWidget),
        ('TechScoreModule', TechScorePDFWidget),
    ]


class ReportMultiPageRenderer(ReportRenderingMixin, BasePageRenderer):
    template_name = "reports/page_display/papersize_container_multigenerated.html"

    replaced_module_widgets = [
        ('TechScoreModule', TechScoreFromIterableWidget)
    ]

    def get_context_data(self, **kwargs):
        kwargs = super(ReportMultiPageRenderer, self).get_context_data(**kwargs)
        kwargs.update({
            'iterable_pages': self.get_elements(kwargs.get('request')),
            'iterable_element_height': 100/self.page.elements_per_page,
        })

        return kwargs

    def get_elements(self, request):
        iterable_pages = []
        inquiry = get_inquiry_from_request(request)
        elements = TechListReportPageRetrieval.get_iterable(inquiry=inquiry, mode=self.page.multi_type)
        num_elements = len(elements)
        for t in range(int(num_elements/self.page.elements_per_page)):
            iterable_pages.append(
                elements[t:t+self.page.elements_per_page]
            )
        remaining = num_elements - int(num_elements/self.page.elements_per_page)*self.page.elements_per_page
        if remaining > 0:
            iterable_pages.append(
                elements[num_elements-remaining:num_elements]
            )

        return iterable_pages


class ReportMultiPagePDFRenderer(ReportMultiPageRenderer):
    replaced_module_widgets = [
        ('ImageModule', ImagePDFWidget),
        ('TechScoreModule', TechScoreFromIterablePDFWidget),
    ]