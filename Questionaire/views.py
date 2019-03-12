from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Page
from django.shortcuts import get_object_or_404
from .forms import QuestionPageForm


# Create your views here.

class QPageView(TemplateView):
    template_name = "question_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.page = get_object_or_404(Page, id=self.kwargs['page'])
        context['form'] = QuestionPageForm(self.page)

        return context

    def post(self, request, *args, **kwargs):
        print(request.POST)

        context = self.get_context_data()


        if 'add_external_submit' in request.POST:
            return self.render_to_response(context)
        else:
            return self.render_to_response(context)
