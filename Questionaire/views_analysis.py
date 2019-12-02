from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView, ListView

from .models import Inquiry, TechGroup, InquiryQuestionAnswer
from .views import SiteBaseTemplateMixin


class SiteDetailView(SiteBaseTemplateMixin, DetailView):
    pass


class AnalysisListView(LoginRequiredMixin, SiteBaseTemplateMixin, ListView):
    template_name = "inquiry_pages/inquiry_analysis_overview.html"
    model = Inquiry


class AnalysisDetailView(LoginRequiredMixin, SiteDetailView):
    pass


class InquiryAnalysis(AnalysisDetailView):
    model = Inquiry
    template_name_field = "inquiry"
    template_name = "inquiry_pages/inquiry_analysis_detail.html"

    def get_context_data(self, **kwargs):
        context = super(InquiryAnalysis, self).get_context_data(**kwargs)
        context['techs'] = TechGroup.objects.all()
        context['DISPLAY_TECH_SCORES'] = True
        context['processed_answers'] = InquiryQuestionAnswer.objects.filter(inquiry=self.object)

        return context


