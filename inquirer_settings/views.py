from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from general.mixins import InquiryMixin
from initiative_enabler.models import TechCollective
from inquirer_settings.forms import *
from inquirer_settings.models import PendingMailVerifyer


class SelectedSubsectionMixin:
    section_name = None

    def get_context_data(self, **kwargs):
        return super(SelectedSubsectionMixin, self).get_context_data(
            section_name=self.section_name,
            **kwargs)


class InquirerSettingsHome(InquiryMixin, SelectedSubsectionMixin, TemplateView):
    template_name = "inquirer_settings/home.html"
    section_name = 'home'


class InquirerMailSettingsView(InquiryMixin, SelectedSubsectionMixin, FormView):
    template_name = "inquirer_settings/mail_settings.html"
    success_url = reverse_lazy("inquirer_settings:mail")
    section_name = 'mail'
    form_class = EmailForm

    def get_context_data(self, **kwargs):
        # Check if a new mail was given even though a previous one was already confirmed.
        # In that case it should keep sending mails to the old address until the new mail adress is confirmed.
        if self.inquirer.email and self.inquirer.email_validated:
            current_pending = PendingMailVerifyer.objects.filter(
                inquirer=self.inquirer,
                active=True,
            ).last()
        else:
            current_pending = None

        return super(InquirerMailSettingsView, self).get_context_data(
            current_pending=current_pending,
            **kwargs
        )

    def get_form_kwargs(self):
        kwargs = super(InquirerMailSettingsView, self).get_form_kwargs()
        kwargs.update({
            'inquirer': self.inquirer,
        })
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(InquirerMailSettingsView, self).form_valid(form)


class ReSendMailValidationView(InquiryMixin, FormView):
    form_class = ResendPendingMailForm
    success_url = reverse_lazy('inquirer_settings:mail')

    def get_form_kwargs(self):
        kwargs = super(ReSendMailValidationView, self).get_form_kwargs()
        kwargs['inquirer'] = self.inquirer
        return kwargs

    def form_valid(self, form):
        form.send()
        messages.success(self.request, 'Wij hebben u een nieuwe e-mail verstuurd met de code')
        return super(ReSendMailValidationView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Wij konden niet de mail versturen")
        return HttpResponseRedirect(redirect_to=self.success_url)


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


"""
Email validation
"""


class EmailValidationView(FormView):
    form_class = PendingMailForm
    template_name = "inquirer_settings/email_validation_screen.html"
    success_url = reverse_lazy('inquirer_settings:validate_mail_success')

    def get_form_kwargs(self):
        kwargs = super(EmailValidationView, self).get_form_kwargs()
        kwargs.setdefault('data', self.request.GET)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(EmailValidationView, self).get_context_data(**kwargs)
        context['email'] = self.request.GET.get('email', None)
        return context

    def form_valid(self, form):
        form.verify()
        return super(EmailValidationView, self).form_valid(form)


class EmailValidationSuccessView(TemplateView):
    template_name = "inquirer_settings/email_validation_screen_success.html"