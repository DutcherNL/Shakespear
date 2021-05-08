import os
import pdfkit

from django.http import FileResponse
from django.conf import settings
from django.utils import timezone
from django.template.loader import get_template

from reports.report_plotter import ReportPlotter
from reports.models import RenderedReport
from Questionaire.utils import get_inquiry_from_request


class SingleUsePDFResponse(FileResponse):
    """ A HTTP Response that returns a pdf file constructed from a HTML template instead of a HTML webpage """

    def __init__(self, request=None, template=None, context=None, using=None, file_name='',
                 page_options=None, **response_kwargs):
        template = get_template(template[0], using=using)
        html = template.render(context=context, request=request)

        # Create a unique copy of the file
        timestamp = timezone.now().timestamp()
        local_file_name = f"{file_name}_{timestamp}.pdf"
        local_file_path = os.path.join(settings.REPORT_ROOT, 'onetime', local_file_name)

        self.save_as_pdf(html, local_file_path, options=page_options)
        super(SingleUsePDFResponse, self).__init__(open(local_file_path, 'rb'))

        self['Content-Type'] = 'application/pdf'
        self['Content-Disposition'] = 'attachment; filename={filename}'.format(filename=f'{file_name}.pdf')

    def save_as_pdf(self, html_layout, filepath, options={}):
        base_options = {
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
        if options:
            base_options.update(options)

        # Create the pdf
        pdfkit.from_string(html_layout, filepath, options=base_options)


class CreatedPDFResponse(FileResponse):
    def __init__(self, request=None, report=None, **response_kwargs):
        plotter = ReportPlotter(report=report)
        inquiry = get_inquiry_from_request(request)

        created_report = plotter.plot_report(inquiry)

        super(CreatedPDFResponse, self).__init__(open(created_report.file.path, 'rb'))

        self['Content-Type'] = 'application/pdf'
        self['Content-Disposition'] = 'attachment; filename={filename}'.format(filename=f'{report.file_name}')


class StoredPDFResponse(FileResponse):
    def __init__(self, created_report=None, **response_kwargs):
        # from reports.models import RenderedReport
        # created_report = RenderedReport.objects.get()

        super(StoredPDFResponse, self).__init__(open(created_report.file.path, 'rb'), **response_kwargs)

        self['Content-Type'] = 'application/pdf'
        self['Content-Disposition'] = 'attachment; filename={filename}'.format(
            filename=f'{created_report.report.file_name}'
        )


class StoredOrCreatePDFRespose(FileResponse):
    """ This returs a rendered Report if oe is availlable. If not it creates a new report and then returns it. """

    def __init__(self, report=None, inquiry=None, **response_kwargs):
        self.report = report
        self.inquiry = inquiry

        print(f'Inquiry -- {inquiry}')

        # Static reports do not use inquiry data
        if self.report.is_static:
            rendered_report = self.get_rendered_static_report()
        else:
            rendered_report = self.get_rendered_user_report()

        super(StoredOrCreatePDFRespose, self).__init__(open(rendered_report.file.path, 'rb'), **response_kwargs)

        self['Content-Type'] = 'application/pdf'
        self['Content-Disposition'] = 'attachment; filename={filename}'.format(
            filename=f'{self.report.file_name}'
        )

    def get_rendered_static_report(self):
        """ Get the static report instance, construct it if neccesary """
        rendered_report = RenderedReport.objects.filter(
            report=self.report,
            created_on__gte=self.report.last_edited
        ).order_by(
            'created_on'
        ).last()

        if rendered_report is None:
            # The file is not yet build, so build the file.
            rendered_report = ReportPlotter(report=self.report).plot_report(inquiry=None)

        return rendered_report

    def get_rendered_user_report(self):
        """ Create or get a plot of the user-specefied report """
        # Make sure that the processed file has the latest changes
        threshold_date = max(self.inquiry.completed_on, self.report.last_edited)

        rendered_report = RenderedReport.objects.filter(
            report=self.report,
            inquiry=self.inquiry,
            created_on__gte=threshold_date
        ).order_by(
            'created_on'
        ).last()

        if rendered_report is None:
            # The file is not yet build, so build the file.
            rendered_report = ReportPlotter(report=self.report).plot_report(inquiry=self.inquiry)

        return rendered_report