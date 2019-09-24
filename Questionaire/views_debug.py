from django.views import View
from django.views.generic import TemplateView
from .models import Page, Inquiry, Technology, Score
from django.shortcuts import get_object_or_404
from .forms import QuestionPageForm, EmailForm, InquiryLoadDebugForm, InquirerLoadForm
from django.http import HttpResponseRedirect
from django.urls import reverse

from .views import *


# Create your views here.


class CreateNewInquiryViewDebug(CreateNewInquiryView):
    def get_redirect(self, request):
        return HttpResponseRedirect(reverse('debug_start_query', kwargs={'inquirer': self.inquirer.id}))


class InquiryStartScreenDebug(InquiryStartScreen):
    def init_base_properties(self):
        self.inquirer = get_object_or_404(Inquirer, id=self.kwargs['inquirer'])

    def redirect_to(self):
        first_page = Page.objects.order_by('position').first()
        return HttpResponseRedirect(reverse('debug_q_page',
                                            kwargs={'inquiry': self.inquirer.active_inquiry.id,
                                                    'page': first_page.id}))


class QueryIndexViewDebug(TemplateView):
    template_name = "front_page.html"
    redirect_to = None

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)

        if self.redirect_to is not None:
            return HttpResponseRedirect(self.redirect_to)

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['inquiries'] = Inquirer.objects.all()
        context['inquiry_entry_form'] = InquiryLoadDebugForm(self.request.GET)

        if context['inquiry_entry_form'].is_valid():
            self.redirect_to = context['inquiry_entry_form'].get_inquiry().get_url()

        return context


class QPageViewDebug(QPageView):
    def init_base_keys(self):
        self.page = get_object_or_404(Page, id=self.kwargs['page'])
        self.inquiry = get_object_or_404(Inquiry, id=self.kwargs['inquiry'])

    def get_redirect(self, get_next):
        page = self.get_page(get_next=get_next)
        return reverse('debug_q_page', kwargs={'inquiry': self.inquiry.id, 'page': page.id})


class InquiryScoresViewDebug(TemplateView):
    template_name = 'inquiry_scores.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.inquiry = get_object_or_404(Inquiry, id=self.kwargs['inquiry'])

        context['inquiry'] = self.inquiry
        context['techs'] = Technology.objects.all()

        return context


class StartViewDebug(TemplateView):
    template_name = "inquiry_pages/start_debug_page.html"