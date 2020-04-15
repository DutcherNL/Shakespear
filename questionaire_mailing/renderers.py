from PageDisplay.renderers import BasePageRenderer
from questionaire_mailing.module_widgets.module_widgets import *


class MailHTMLRenderer(BasePageRenderer):
    template_name = "questionaire_mailing/mails/base_html.html"

    replaced_module_widgets = [
        ('TitleModule', MailedHTMLTitleWidget),
        ('TextModule', MailedHTMLTextWidget)
    ]


class MailPlainRenderer(BasePageRenderer):
    template_name = "questionaire_mailing/mails/base_plain.txt"

    replaced_module_widgets = [
        ('TitleModule', MailedPlainTitleWidget),
        ('TextModule', MailedPlainTextWidget)
    ]