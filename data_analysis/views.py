import urllib
from django.views.generic import TemplateView


from .forms import *


class TestView(TemplateView):
    template_name = "data_analysis/data_analysis_inquiry_progress.html"
    form_classes = [InquiryCreatedFilterForm, InquiryLastVisitedFilterForm, InquiryUserExcludeFilterForm]

    def get_context_data(self, **kwargs):
        context = super(TestView, self).get_context_data()

        get_data = self.request.GET if self.request.GET else None
        forms = []
        for form_class in self.form_classes:
            form = form_class(get_data)
            if form.has_filter_data():
                context['inquiries'] = form.get_filtered_inquiries()
            forms.append(form)

        context['query_line'] = urllib.parse.urlencode(self.request.GET)

        context['forms'] = forms

        return context


