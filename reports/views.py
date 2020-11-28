from django.shortcuts import render

import os

from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin

from Questionaire.views import QuestionaireCompleteView
from .models import Report, ReportPage, PageCriteria

# Create your views here.


# Todo: Check if these views can be redacted. They don't seem to be used in an active manor

class QuestionaireCompletePDFView(LoginRequiredMixin, QuestionaireCompleteView):
    template_name = "report_preview.html"

    def dispatch(self, request, *args, **kwargs):
        self.init_keys()
        return super(QuestionaireCompletePDFView, self).dispatch(request, *args, **kwargs)

    def init_keys(self):
        if self.kwargs.get('page_number', None):
            self.page = ReportPage.objects.filter(page_number=self.kwargs['page_number']).order_by('last_edited').first()
        else:
            print("No page number")
            self.page = None

    def get_context_data(self, **kwargs):
        context = super(QuestionaireCompletePDFView, self).get_context_data(**kwargs)
        context['pages'] = ReportPage.objects.filter(report__is_live=True).order_by('reportpagelink__page_number')
        if self.page:
            context['pages'] = context['pages'].filter(
                reportpagelink__page_number=self.page.page_number,
                reportpagelink__report=self.report,
            )
        else:
            context['show_overview'] = True

        return context


class ResultsPDFPlotter(QuestionaireCompleteView):
    template_name = "report_overview.html"
    template_engine = "PDFTemplates"

    def dispatch(self, request, *args, **kwargs):
        super(ResultsPDFPlotter, self).dispatch(request, *args, **kwargs)

        from django.template.loader import get_template
        import pdfkit

        template = get_template(self.template_name, using=self.template_engine)
        context = self.get_context_data()
        html = template.render(context)  # Renders the template with the context data.

        timestamp = timezone.now().timestamp()
        filename = "{id}-{timestamp}.pdf".format(id=self.inquiry.id, timestamp=timestamp)
        filepath = os.path.join(settings.REPORT_ROOT, filename)

        options = {
            'page-size': 'A4',
            'margin-top': '0in',
            'margin-right': '0in',
            'margin-bottom': '0in',
            'margin-left': '0in',
            'minimum-font-size': '12',
            'viewport-size': '1280x1024'
        }

        #pdfkit.from_url('https://www.papersizes.org/a-paper-sizes.htm', filepath)
        pdfkit.from_string(html, filepath)

        pdf = open(filepath, 'rb')
        response = HttpResponse(content=pdf)  # Generates the response as pdf response.
        response['Content-Type'] = 'application/pdf'
        response['Content-Disposition'] = 'attachment; filename={filename}'.format(filename=filename)
        pdf.close()
        # remove the locally created pdf file.
        # os.remove(filepath)

        return response  # returns the response.