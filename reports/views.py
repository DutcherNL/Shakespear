from django.shortcuts import render

import os

from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone

from Questionaire.views import QuestionaireCompleteView
from .models import Report, Page, PageCriteria

# Create your views here.


class QuestionaireCompletePDFView(QuestionaireCompleteView):
    template_name = "report_overview.html"

    def get_context_data(self, **kwargs):
        context = super(QuestionaireCompletePDFView, self).get_context_data(**kwargs)
        context['pages'] = Page.objects.filter(report__is_live=True).order_by('page_number')

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