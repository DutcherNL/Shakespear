import os
import pdfkit

from django.http import FileResponse
from django.conf import settings
from django.utils import timezone
from django.template.loader import get_template


class PDFResponse(FileResponse):
    """ A HTTP Response that returns a pdf file constructed from a HTML template instead of a HTML webpage """

    def __init__(self, request=None, template=None, context=None, using=None, file_name='', **response_kwargs):
        template = get_template(template[0], using=using)
        html = template.render(context=context, request=request)

        # Create a unique copy of the file
        timestamp = timezone.now().timestamp()
        local_file_name = f"{file_name}_{timestamp}.pdf"
        local_file_path = os.path.join(settings.REPORT_ROOT, local_file_name)

        self.save_as_pdf(html, local_file_path)
        super(PDFResponse, self).__init__(open(local_file_path, 'rb'))

        self['Content-Type'] = 'application/pdf'
        self['Content-Disposition'] = 'attachment; filename={filename}'.format(filename=f'{file_name}.pdf')

    def save_as_pdf(self, html_layout, filepath, options=None):
        options = options or {
            'page-size': 'A4',
            'orientation': 'Portrait',
            'margin-top': '0in',
            'margin-right': '0in',
            'margin-bottom': '0in',
            'margin-left': '0in',
            'disable-smart-shrinking': None,
            'zoom': 1,  # Correction for windows display due to different dpi (96dpi) with linux (75dpi)
        }
        # Create the pdf
        pdfkit.from_string(html_layout, filepath, options=options)

