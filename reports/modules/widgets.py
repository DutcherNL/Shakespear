from PageDisplay.module_widgets import ImageWidget
from Questionaire.modules.widgets import TechScoreWidget


class TechScorePDFWidget(TechScoreWidget):
    template_name = "modules/module_tech_score_forPDF.html"

class TechScorePreviewPDFWidget(TechScoreWidget):
    template_name = "modules/module_tech_score_forPDF_preview.html"


class ImagePDFWidget(ImageWidget):
    template_name = "modules/module_image_forPDF.html"
