from PageDisplay.renderers import BasePageRenderer


class InquiryPagePreviewRenderer(BasePageRenderer):
    template_name = "inquiry/questionaire_question_setup_page.html"


class InquiryPageRenderer(BasePageRenderer):
    template_name = "inquiry/questionaire_question_page.html"
