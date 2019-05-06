from django.views import View
from django.views.generic import TemplateView
from .models import Page, Inquiry, TechnologyScore, Technology
from django.shortcuts import get_object_or_404
from .forms import QuestionPageForm
from django.http import HttpResponseRedirect
from django.urls import reverse


# Create your views here.

class QPageView(TemplateView):
    template_name = "question_page.html"

    def setup(self, *args, **kwargs):
        super(QPageView, self).setup(*args, **kwargs)

        self.page = get_object_or_404(Page, id=self.kwargs['page'])
        self.inquiry = get_object_or_404(Inquiry, id=self.kwargs['inquiry'])

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if not self.page.is_valid_for_inquiry(self.inquiry):
            nextid = self.get_page(get_next=True).id
            return HttpResponseRedirect(reverse('q_page', kwargs={'inquiry': self.inquiry.id, 'page': nextid}))

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['form'] = QuestionPageForm(self.page, self.inquiry)

        context['has_prev_page'] = self.get_page(get_next=False) is not None
        context['has_next_page'] = self.get_page(get_next=True) is not None

        context['tech_scores'] = TechnologyScore.objects.filter(inquiry=self.inquiry)

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        context['form'] = QuestionPageForm(self.page, self.inquiry, request.POST)

        if context['form'].is_valid():
            context['form'].save(self.inquiry)

            if 'prev' in request.POST:
                print("PREV")
                context['form'].backward(self.inquiry)
                rev = self.get_reverse(self.get_page(get_next=False))
                return HttpResponseRedirect(rev)
            else:
                print("NEXT")
                context['form'].forward(self.inquiry)
                rev = self.get_reverse(self.get_page(get_next=True))
                return HttpResponseRedirect(rev)

        return self.render_to_response(context)

    def get_reverse(self, page):
        return reverse('q_page', kwargs={'inquiry': self.inquiry.id, 'page': page.id})

    def get_page(self, get_next=True):
        if get_next:
            return Page.objects.filter(position__gt=self.page.position).order_by('position').first()
        else:
            return Page.objects.filter(position__lt=self.page.position).order_by('position').last()


class QueryIndexView(TemplateView):
    template_name = "front_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['inquiries'] = Inquiry.objects.all()

        return context


class CreateNewInquiryView(View):

    def post(self, request):
        inquiry = Inquiry()
        inquiry.save()
        return HttpResponseRedirect(reverse('q_page', kwargs={'inquiry': inquiry.id, 'page': 1}))


class TechDetailsView(TemplateView):
    template_name = "technology_info.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.technology = get_object_or_404(Technology, id=self.kwargs['tech_id'])
        context['technology'] = self.technology

        return context