from PageDisplay.renderers import BasePageRenderer
from questionaire_mailing.modules.module_widgets import *


class MailHTMLRenderer(BasePageRenderer):
    template_name = "questionaire_mailing/mails/base_html.html"

    replaced_module_widgets = [
        ('TitleModule', MailedHTMLTitleWidget),
        ('TextModule', MailedHTMLTextWidget),
        ('VerticalContainerModule', MailedHTMLVerticalContainerWidget)
    ]


class MailPlainRenderer(BasePageRenderer):
    template_name = "questionaire_mailing/mails/base_plain.txt"

    replaced_module_widgets = [
        ('TitleModule', MailedPlainTitleWidget),
        ('TextModule', MailedPlainTextWidget),
        ('InquirerCodeModule', MailedPlainInquirerCodeWidget),
        ('VerticalContainerModule', MailedPlainVerticalContainerWidget)
    ]
