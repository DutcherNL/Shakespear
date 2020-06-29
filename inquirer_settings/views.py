from django.views.generic import TemplateView, FormView

from general.mixins import InquiryMixin
from initiative_enabler.models import TechCollective, TechCollectiveInterest
from Questionaire.models import InquiryQuestionAnswer
from inquirer_settings.forms import *


class SelectedSubsectionMixin:
    section_name = None

    def get_context_data(self, **kwargs):
        return super(SelectedSubsectionMixin, self).get_context_data(
            section_name=self.section_name,
            **kwargs)


class InquirerSettingsHome(InquiryMixin, SelectedSubsectionMixin, TemplateView):
    template_name = "inquirer_settings/home.html"
    section_name = 'home'


class InquirerMailSettingsView(InquiryMixin, SelectedSubsectionMixin, TemplateView):
    template_name = "inquirer_settings/mail_settings.html"
    section_name = 'mail'


class CollectiveInterestView(InquiryMixin, SelectedSubsectionMixin, TemplateView):
    template_name = "inquirer_settings/collective_interest.html"
    section_name = 'tech_cols'

    def get_context_data(self, **kwargs):
        return super(CollectiveInterestView, self).get_context_data(
            tech_cols=TechCollective.objects.order_by('technology__name'),
            **kwargs
        )


class InquirerAnswersView(InquiryMixin, SelectedSubsectionMixin, FormView):
    template_name = "inquirer_settings/answers_overview.html"
    form_class = RemoveInquiryDataForm
    section_name = 'answers'

    def get_form_kwargs(self):
        kwargs = super(InquirerAnswersView, self).get_form_kwargs()
        kwargs.update({
            'inquiry': self.inquiry,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        answers = InquiryQuestionAnswer.objects.filter(
            inquiry=self.inquiry,
            answer__isnull=False,
        ).prefetch_related('question')

        return super(InquirerAnswersView, self).get_context_data(
            answers=answers,
            **kwargs
        )

    def form_valid(self, form):
        form.delete()
        return super(InquirerAnswersView, self).form_valid(form)
