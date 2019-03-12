from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Page
from django.shortcuts import get_object_or_404
from .forms import QuestionPageForm
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse


# Create your views here.

class QPageView(TemplateView):
    template_name = "question_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.page = get_object_or_404(Page, id=self.kwargs['page'])
        context['form'] = QuestionPageForm(self.page)

        context['has_prev_page'] = Page.objects.filter(position__lt=self.page.position).count() > 0
        context['has_next_page'] = Page.objects.filter(position__gt=self.page.position).count() > 0

        return context

    def post(self, request, *args, **kwargs):
        print(request.POST)

        context = self.get_context_data()

        if context['form'].is_valid() or True:
            # Todo: save form

            if 'prev' in request.POST:
                print("PREV")
                rev = reverse('q_page', kwargs={'page': self.get_page(get_next=False).id})
                return HttpResponseRedirect(rev)
            else:
                print("NEXT")
                rev = reverse('q_page', kwargs={'page': self.get_page().id})
                return HttpResponseRedirect(rev)

        return self.render_to_response(context)

    def get_page(self, get_next=True):
        if get_next:
            return Page.objects.filter(position__gt=self.page.position).order_by('position').first()
        else:
            return Page.objects.filter(position__lt=self.page.position).order_by('position').last()
