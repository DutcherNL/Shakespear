from django.views import View
from django.views.generic import TemplateView
from .models import Page, Inquiry, Technology, Score
from django.shortcuts import get_object_or_404
from .forms import QuestionPageForm, EmailForm, InquiryLoadDebugForm, InquiryLoadForm
from django.http import HttpResponseRedirect
from django.urls import reverse


# Create your views here.


class CreateNewInquiryView(View):
    def post(self, request):
        self.inquiry = Inquiry()
        self.inquiry.save()

        return self.get_redirect(request)

    def get_redirect(self, request):
        request.session['inquiry_id'] = self.inquiry.id

        return HttpResponseRedirect(reverse('start_query'))


class InquiryStartScreen(TemplateView):
    template_name = "inquiry_start.html"

    def get_context_data(self, **kwargs):
        context = super(InquiryStartScreen, self).get_context_data(**kwargs)

        self.init_base_properties()

        context['inquiry'] = self.inquiry
        context['form'] = EmailForm(inquiry=context['inquiry'])

        return context

    def init_base_properties(self):
        self.inquiry = get_object_or_404(Inquiry, id=self.request.session.get('inquiry_id', None))

    def redirect_to(self):
        first_page = Page.objects.order_by('position').first()
        self.request.session['page_id'] = first_page.id
        return HttpResponseRedirect(reverse('run_query'))

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        print(request.POST)

        # Add the comment
        form = EmailForm(inquiry=context['inquiry'], data=request.POST)

        if form.is_valid():
            form.save()
            return self.redirect_to()
        else:
            context['form'] = form
            return self.render_to_response(context)


class QPageView(TemplateView):
    template_name = "question_page.html"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if self.page.is_valid_for_inquiry(self.inquiry):
            if self.page.auto_process and self.inquiry.current_page.position != self.page.position:
                form = QuestionPageForm(self.page, self.inquiry, request.GET)
                if form.is_valid():
                    # The form is valid, the page should not be displayed visibly
                    form.save(self.inquiry)

                    # Determine whether the movement is forward or backward
                    if self.inquiry.current_page.position < self.page.position:
                        # Movement is forward
                        form.forward(self.inquiry)
                        rev = self.get_reverse(self.get_page(get_next=True))
                        return HttpResponseRedirect(rev)
                    if self.inquiry.current_page.position > self.page.position:
                        # Movement is backward
                        form.backward(self.inquiry)
                        rev = self.get_reverse(self.get_page(get_next=False))
                        return HttpResponseRedirect(rev)

            # The page should be displayed normally
            self.inquiry.set_current_page(self.page)

            return response
        else:
            if self.inquiry.current_page.position < self.page.position:
                return HttpResponseRedirect(self.get_redirect(True))
            else:
                return HttpResponseRedirect(self.get_redirect(False))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.init_base_keys()

        context['form'] = QuestionPageForm(self.page, self.inquiry)

        context['has_prev_page'] = self.get_page(get_next=False) is not None
        context['has_next_page'] = self.get_page(get_next=True) is not None

        context['inquiry'] = self.inquiry
        context['techs'] = Technology.objects.all()

        # context['tech_scores'] = TechnologyScore.objects.filter(inquiry=self.inquiry)

        return context

    def init_base_keys(self):
        self.page = get_object_or_404(Page, id=self.request.session.get('page_id', None))
        self.inquiry = get_object_or_404(Inquiry, id=self.request.session.get('inquiry_id', None))

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        context['form'] = QuestionPageForm(self.page, self.inquiry, request.POST)

        if context['form'].is_valid():
            context['form'].save(self.inquiry)

            if 'prev' in request.POST:
                context['form'].backward(self.inquiry)
                return HttpResponseRedirect(self.get_redirect(False))
            else:
                context['form'].forward(self.inquiry)
                return HttpResponseRedirect(self.get_redirect(True))

        return self.render_to_response(context)

    def get_redirect(self, get_next):
        page = self.get_page(get_next=get_next)

        self.request.session['page_id'] = page.id

        return reverse('run_query')

    def get_page(self, get_next=True):
        if get_next:
            return Page.objects.filter(position__gt=self.page.position).order_by('position').first()
        else:
            return Page.objects.filter(position__lt=self.page.position).order_by('position').last()


class TechDetailsView(TemplateView):
    template_name = "technology_info.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.technology = get_object_or_404(Technology, id=self.kwargs['tech_id'])
        context['technology'] = self.technology

        return context


class QuesetionHomeScreenView(TemplateView):
    template_name = "inquiry_pages/inquiry_home.html"

    redirect_to = None

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)

        if self.redirect_to is not None:
            return HttpResponseRedirect(self.redirect_to)

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['inquiries'] = Inquiry.objects.all()
        context['inquiry_entry_form'] = InquiryLoadForm(self.request.GET)

        if context['inquiry_entry_form'].is_valid():
            self.request.session['value'] = context['inquiry_entry_form'].get_code_value()

        context['session_value'] = self.request.session.get('value', "Not defined")

        return context