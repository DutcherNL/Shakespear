import urllib
from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin

from Questionaire.models import Technology
from .forms import *
from .models import QuestionFilter
from . import MIN_INQUIRY_REQ


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
            if form_class.can_filter(data=get_data, **self.get_form_kwargs(form_class)):
                form = form_class(get_data, **self.get_form_kwargs(form_class))
                forms.append(form)

        # Get the current inquiry dataset
        inquiries = None
        for form in forms:
            inquiries = form.get_filtered_inquiries(inquiries=inquiries)
        context['inquiries'] = inquiries
        context['MIN_INQUIRY_REQ'] = MIN_INQUIRY_REQ

        # The get query parameters in url query format to be used when calling graph data
        context['query_line'] = urllib.parse.urlencode(self.request.GET)

        context['forms'] = forms

        return context

    def get_form_kwargs(self, form_class):
        return {}


class InquiryDataView(FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_inquiry_progress.html"
    form_classes = [InquiryLastVisitedFilterForm, InquiryUserExcludeFilterForm, FilterInquiryByQuestionForm]

    def get_form_kwargs(self, form_class):
        kwargs = super(InquiryDataView, self).get_form_kwargs(form_class)
        if form_class is FilterInquiryByQuestionForm:
            kwargs.update({
                'filter_models': QuestionFilter.objects.filter(use_for_progress_analysis=True)
            })
        return kwargs


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
                'filter_models': QuestionFilter.objects.filter(use_for_tech_analysis=True)
            })
        return kwargs