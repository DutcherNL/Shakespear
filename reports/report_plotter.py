import os
import pdfkit

from django.conf import settings
from django.core.files import File
from django.utils import timezone
from django.template.loader import get_template

from reports.renderers import ReportSinglePagePDFRenderer
from reports.models import RenderedReport


class ReportPlotter:
    """ A HTTP Response that returns a pdf file constructed from a HTML template instead of a HTML webpage """
    template_name = "reports/pdf_report.html"
    template_engine = "PDFTemplates"
    page_renderer_class = ReportSinglePagePDFRenderer
    file_name = "test_report"
    report = None
    pdf_options = {}

    def __init__(self, report, using=None):
        assert report is not None
        self.report = report
        if using:
            self.template_engine = using

    def plot_report(self, inquiry=None, file_name=None):
        """ Plots the report to a file and strores a reference in the database """

        # Create the plotting file
        plotted_report = RenderedReport.objects.create(
            report=self.report,
            inquiry=inquiry,
        )

        # Create the HTML content which is to be plotted to the PDF
        html_content = self.plot_report_as_html(self.get_context_data(inquiry=inquiry))

        # Ensure a (likely) unique name by including a timestamp
        timestamp = timezone.now().timestamp()
        file_name = file_name or self.file_name
        if inquiry:
            local_file_name = f"{file_name}_{inquiry.id}_{timestamp}.pdf"
        else:
            local_file_name = f"{file_name}_{timestamp}.pdf"
        # For maintenance and privacy reasons the reports are stored elsewhere at REPORT_ROOT
        local_file_path = os.path.join(settings.REPORT_ROOT, local_file_name)
        self.save_as_pdf(html_content, local_file_path)

        # Update the database with a reference to the file
        plotted_report.file.name = local_file_name
        plotted_report.save()

        return local_file_path

    def plot_report_as_html(self, context):
        """ Plots the report in HTML format ready for PDF translation """
        template = get_template(self.template_name, using=self.template_engine)
        html = template.render(context=context)
        return html

    def get_context_data(self, inquiry=None):
        return {
            'template_engine': self.template_engine,
            'report': self.report,
            'renderer': self.page_renderer_class,
            'inquiry': inquiry,
        }

    def save_as_pdf(self, html_layout, filepath):
        pdfkit_options = {
            'dpi': 96,  # Set DPI to a fixed value to correspond with Windows (vital for things like line-width)
            'page-size': 'A4',
            'orientation': 'Portrait',
            'margin-top': '0in',
            'margin-right': '0in',
            'margin-bottom': '0in',
            'margin-left': '0in',
            'disable-smart-shrinking': None,
            'zoom': 1,  # Correction for windows display due to different dpi (96dpi) with linux (75dpi)
        }
        pdfkit_options.update(self.pdf_options)

        # Create the pdf
        pdfkit.from_string(html_layout, filepath, options=pdfkit_options)
