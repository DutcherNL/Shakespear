from PageDisplay.module_widgets import ImageWidget
from Questionaire.modules.widgets import TechScoreWidget
from Questionaire.models import Technology

__all__ = ['TechScorePDFWidget', 'TechScorePreviewPDFWidget', 'ImagePDFWidget', 'TechScoreFromIterableWidget',
           'TechScoreFromIterablePDFWidget']


class TechScorePDFWidget(TechScoreWidget):
    template_name = "modules/module_tech_score_forPDF.html"


class TechScorePreviewPDFWidget(TechScoreWidget):
    template_name = "modules/module_tech_score_forPDF_preview.html"


class ImagePDFWidget(ImageWidget):
    template_name = "modules/module_image_forPDF.html"


class TechScoreFromIterableWidget(TechScoreWidget):
    use_from_context = ['iterable_content', ]

    def get_context_data(self, request=None, **kwargs):
        context = super(TechScoreFromIterableWidget, self).get_context_data(request)
        context['technology'] = Technology.objects.get(id=kwargs.get('iterable_content').id)
        return context


class TechScoreFromIterablePDFWidget(TechScoreFromIterableWidget):
    template_name = "modules/module_tech_score_forPDF.html"

    def get_context_data(self, request=None, **kwargs):
        return super(TechScoreFromIterablePDFWidget, self).get_context_data(request=request, **kwargs)