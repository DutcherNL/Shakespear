from django.db import models

from PageDisplay.models import VerticalModuleContainer


class PageContainer(VerticalModuleContainer):
    template_name = 'reports/page_display/papersize_container.html'

    PAPER_SIZES = [
        ('A3', 'A3 (297 x 420mm)'),
        ('A4', 'A4 (210 x 297mm)'),
        ('A5', 'A5 (148 x 210mm)'),
    ]
    size = models.CharField(max_length=3, choices=PAPER_SIZES, default='A4')
    orientation = models.BooleanField(choices=[
        (True, "Standing"),
        (False, "Rotated")], default=True)


    def get_context_data(self, *args, **kwargs):
        context = super(PageContainer, self).get_context_data(*args, **kwargs)
        context['measurements'] = {
            'margins': "20mm 20mm 20mm 20mm",
            'size': self.paper_proportions
        }
        return context

    @property
    def paper_proportions(self):
        """ Returns a dict of the height and width of the pgae"""
        if self.size == 'A3':
            size = ("297mm", "420mm")
        if self.size == 'A4':
            sizes = ("210mm", "297mm")
        if self.size == 'A5':
            sizes = ("148mm", "210mm")

        if self.orientation:
            return {'width': sizes[0], 'height': sizes[1]}
        return {'width': sizes[1], 'height': sizes[0]}
