from PageDisplay.module_widgets import TitleWidget, TextWidget

__all__ = ['MailedHTMLTitleWidget', 'MailedHTMLTextWidget', 'MailedPlainTitleWidget', 'MailedPlainTextWidget']


class MailedHTMLTitleWidget(TitleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_html_title.html"


class MailedHTMLTextWidget(TextWidget):
    template_name = "questionaire_mailing/modules/module_mailed_html_text.html"


class MailedPlainTitleWidget(TitleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_plain_title.html"


class MailedPlainTextWidget(TextWidget):
    template_name = "questionaire_mailing/modules/module_mailed_plain_text.html"

