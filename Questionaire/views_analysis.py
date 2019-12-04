from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView, ListView
from django.urls import reverse
from django.contrib import messages

from .models import Inquiry, TechGroup, InquiryQuestionAnswer
from .views import SiteBaseTemplateMixin
from .forms import InquiryMailForm

from mailing.views import ConstructMailView


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


class ConstructMailForInquiryView(SingleObjectMixin, ConstructMailView):
    form_class = InquiryMailForm
    model = Inquiry
    template_name_field = "inquiry"
    template_name = "inquiry_pages/inquiry_analysis-mail.html"
    object = None

    def get_initial(self):
        initial = super(ConstructMailForInquiryView, self).get_initial()
        initial['to'] = self.get_object().inquirer.email
        return initial

    def get_context_data(self, **kwargs):
        # Make sure that the inquiry object is stored before retrieving the context
        # (this is not part of the base mixin, but the base mixin does rely on it)
        self.object = self.get_object()
        return super(ConstructMailForInquiryView, self).get_context_data(**kwargs)

    def get_success_url(self):
        message = "Mail is succesvol verzonden"
        messages.success(self.request, message)

        return reverse('analysis_detail', kwargs={'pk': self.get_object().pk})


