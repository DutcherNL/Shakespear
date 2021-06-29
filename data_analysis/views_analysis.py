from django.views.generic.detail import SingleObjectMixin
from django.views.generic import DetailView, ListView, FormView
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin

from Questionaire.models import Inquiry, Technology, InquiryQuestionAnswer
from Questionaire.views import FlexCssMixin
from Questionaire.forms import InquiryMailForm

from general.mixins.view_mixins import QuickEditMixin

from mailing.views import ConstructMailView

from data_analysis.forms import ActivateInquirerForm


class AccessRestrictionMixin(PermissionRequiredMixin):
    """ A view that restricts access to only those who are authorized """
    permission_required = 'auth.can_access_entry_analysis'


class SiteDetailView(FlexCssMixin, AccessRestrictionMixin, DetailView):
    pass


class AnalysisListView(AccessRestrictionMixin, FlexCssMixin, ListView):
    template_name = "data_analysis/inquiry_analysis_overview.html"
    model = Inquiry

    def get_queryset(self):
        queryset = super(AnalysisListView, self).get_queryset()
        # queryset = queryset.filter(inquirer__user=self.request.user)
        return queryset


class InquiryAnalysis(SiteDetailView):
    model = Inquiry
    template_name_field = "inquiry"
    template_name = "data_analysis/inquiry_analysis_detail.html"

    def get_context_data(self, **kwargs):
        context = super(InquiryAnalysis, self).get_context_data(**kwargs)
        context['techs'] = Technology.objects.all()
        context['DISPLAY_TECH_SCORES'] = True
        context['processed_answers'] = InquiryQuestionAnswer.objects.filter(inquiry=self.object)

        return context


class ActivateInquirerView(SingleObjectMixin, QuickEditMixin, FormView):
    form_class = ActivateInquirerForm
    model = Inquiry

    def get_success_url(self):
        return reverse('data_analysis:analysis_overview')

    def get_form_kwargs(self):
        kwargs = super(ActivateInquirerView, self).get_form_kwargs()
        kwargs.update({
            'current_user': self.request.user,
            'inquirer': self.get_object().inquirer,
        })
        return kwargs

    def form_valid(self, form):
        form.activate_for_session(self.request)
        return super(ActivateInquirerView, self).form_valid(form)


class ConstructMailForInquiryView(SingleObjectMixin, AccessRestrictionMixin, ConstructMailView):
    form_class = InquiryMailForm
    model = Inquiry
    template_name_field = "inquiry"
    template_name = "data_analysis/inquiry_analysis-mail.html"
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


