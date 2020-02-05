import os

from django.views.generic import ListView, CreateView, TemplateView, View
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone

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


class PrintPageAsPDFView(ReportPageMixin, TemplateView):
    template_name = "reports/pdf_page.html"
    template_engine = "PDFTemplates"

    def dispatch(self, request, *args, **kwargs):
        temp_response = super(PrintPageAsPDFView, self).dispatch(request, *args, **kwargs)

        from django.template.loader import get_template
        import pdfkit

        template = get_template(self.template_name, using=self.template_engine)
        context = self.get_context_data()
        html = template.render(context)  # Renders the template with the context data.

        timestamp = timezone.now().timestamp()
        filename = "{id}-{timestamp}.pdf".format(id=self.report_page.id, timestamp=timestamp)
        filepath = os.path.join(settings.REPORT_ROOT, filename)

        #
        #
        options = {
            'page-size': 'A4',
            'orientation': 'Portrait',
            'margin-top': '0in',
            'margin-right': '0in',
            'margin-bottom': '0in',
            'margin-left': '0in',
            'disable-smart-shrinking': None,
            'zoom': 1,  # Correction for windows display due to different dpi (96dpi) with linux (75dpi)
        }

        #pdfkit.from_url('https://www.papersizes.org/a-paper-sizes.htm', filepath)
        pdfkit.from_string(html, filepath, options=options)

        pdf = open(filepath, 'rb')
        response = HttpResponse(content=pdf)  # Generates the response as pdf response.
        response['Content-Type'] = 'application/pdf'
        response['Content-Disposition'] = 'attachment; filename={filename}'.format(filename=filename)
        pdf.close()
        # remove the locally created pdf file.
        # os.remove(filepath)

        return response  # returns the response.

    def get_context_data(self):
        context = super(PrintPageAsPDFView, self).get_context_data()
        context['template_engine'] = self.template_engine
        return context


class PrintPageAsHTMLView(ReportPageMixin, TemplateView):
    template_name = "reports/pdf_page.html"
    template_engine = "PDFTemplates"