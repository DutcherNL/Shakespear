from django.views.generic import ListView, CreateView, DetailView, TemplateView
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import Report, ReportPage


class ReportsOverview(ListView):
    template_name = "reports/reports_overview.html"
    context_object_name = "reports"
    model = Report


class AddReportView(CreateView):
    model = Report
    fields = ['report_name', 'description', 'file_name']

    def get_success_url(self):
        url_kwargs = {
            'report_slug': self.object.slug
        }
        return reverse("setup:reports:details", kwargs=url_kwargs)


class ReportMixin:
    report = None

    def dispatch(self, request, *args, **kwargs):
        self.report = get_object_or_404(Report, slug=kwargs.pop('report_slug'))
        return super(ReportMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self):
        context = super(ReportMixin, self).get_context_data()
        context['report'] = self.report
        return context


class ReportInfoView(ReportMixin, TemplateView):
    template_name = "reports/report_detail.html"


class AddReportPageView(ReportMixin, CreateView):
    model = ReportPage
    fields = ['name', 'description', 'page_number']

    def form_valid(self, form):
        form.instance.report = self.report
        return super(AddReportPageView, self).form_valid(form)

    def get_initial(self):
        initials = super(AddReportPageView, self).get_initial()
        initials['report'] = self.report
        return initials

    def get_success_url(self):
        url_kwargs = {
            'report_slug': self.report.slug,
            'report_page_id': self.object.id
        }
        return reverse("setup:reports:details", kwargs=url_kwargs)


class ReportPageMixinPrep:
    report_page = None

    def dispatch(self, request, *args, **kwargs):
        print(f'KW: {kwargs}')
        self.report_page = get_object_or_404(ReportPage, id=kwargs.pop('report_page_id'), report=self.report)
        return super(ReportPageMixinPrep, self).dispatch(request, *args, **kwargs)

    def get_context_data(self):
        context = super(ReportPageMixinPrep, self).get_context_data()
        context['report_page'] = self.report_page
        return context


class ReportPageMixin(ReportMixin, ReportPageMixinPrep):
    # It is done this way to ensure that the link report_page and report is confirmed before anything else is done
    pass


class ReportPageInfoView(ReportPageMixin, TemplateView):
    template_name = "reports/reportpage_detail.html"

