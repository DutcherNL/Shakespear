import urllib
from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin

from Questionaire.models import Technology
from .forms import *
from .models import QuestionFilter


class AccessRestrictionMixin(PermissionRequiredMixin):
    """ A view that restricts access to only those who are authorized """
    permission_required = 'auth.can_access_data_analysis_pages'


class FilterDataMixin:
    form_classes = []

    def get_context_data(self, **kwargs):
        context = super(FilterDataMixin, self).get_context_data(**kwargs)

        get_data = self.request.GET if self.request.GET else None
        forms = []
        for form_class in self.form_classes:
            form = form_class(get_data, **self.get_form_kwargs(form_class))
            if form.has_filter_data():
                context['inquiries'] = form.get_filtered_inquiries()
            forms.append(form)

        # The get query parameters in url query format to be used when calling graph data
        context['query_line'] = urllib.parse.urlencode(self.request.GET)

        context['forms'] = forms

        return context

    def get_form_kwargs(self, form_class):
        return {}


class InquiryDataView(FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_inquiry_progress.html"
    form_classes = [InquiryCreatedFilterForm, InquiryLastVisitedFilterForm, InquiryUserExcludeFilterForm]


class TechDataView(AccessRestrictionMixin, FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_techs.html"
    form_classes = [InquiryLastVisitedFilterForm,
                    FilterInquiryByQuestionForm, InquiryUserExcludeFilterForm]

    def get_context_data(self, **kwargs):
        return super(TechDataView, self).get_context_data(
            techs=Technology.objects.all(),
            **kwargs
        )

    def get_form_kwargs(self, form_class):
        kwargs = super(TechDataView, self).get_form_kwargs(form_class)
        if form_class is FilterInquiryByQuestionForm:
            kwargs.update({
                'filter_models': QuestionFilter.objects.all()
            })
        return kwargs