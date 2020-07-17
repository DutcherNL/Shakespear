import urllib
from django.views.generic import TemplateView


from .forms import InquiryFilterForm


class TestView(TemplateView):
    template_name = "data_analysis/data_analysis_base.html"

    def get_context_data(self, **kwargs):
        context = super(TestView, self).get_context_data()

        inquiries = None

        if self.request.GET:
            form = InquiryFilterForm(self.request.GET)
            if form.is_valid():
                context['inquiries'] = form.get_ranged_inquiries()
                context['form_valid'] = True

                context['query_line'] = urllib.parse.urlencode(self.request.GET)
        else:
            form = InquiryFilterForm()
        context['form'] = form

        return context


