from PageDisplay.module_widgets import BaseModuleWidget
from PageDisplay.module_widgets import TitleWidget, TextWidget

from Questionaire.models import Inquirer

__all__ = ['MailedHTMLTitleWidget', 'MailedHTMLTextWidget',
           'MailedPlainTitleWidget', 'MailedPlainTextWidget',
           'MailedHTMLInquirerCodeWidget', 'MailedPlainInquirerCodeWidget',
           'MailedPlainVerticalContainerWidget', 'MailedHTMLVerticalContainerWidget']


class MailedHTMLTitleWidget(TitleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_html_title.html"


class MailedHTMLTextWidget(TextWidget):
    template_name = "questionaire_mailing/modules/module_mailed_html_text.html"


class MailedPlainTitleWidget(TitleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_plain_title.html"


class MailedPlainTextWidget(TextWidget):
    template_name = "questionaire_mailing/modules/module_mailed_plain_text.html"


class InquirerCodeWidgetMixin:
    use_from_context = ['inquirer', 'inquiry']

    def get_context_data(self, request=None, inquirer=None, inquiry=None, **kwargs):
        context = super(InquirerCodeWidgetMixin, self).get_context_data(request=request, **kwargs)

        if inquirer:
            context['inquirer_code'] = inquirer.get_inquiry_code()
        elif inquiry:
            context['inquirer_code'] = inquiry.inquirer.get_inquiry_code()
        else:
            context['inquirer_code'] = "code onbekend (oeps, foutje)"
        return context


class MailedHTMLInquirerCodeWidget(InquirerCodeWidgetMixin, BaseModuleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_html_inquirer_code.html"


class MailedPlainInquirerCodeWidget(InquirerCodeWidgetMixin, BaseModuleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_plain_inquirer_code.html"


class MailedHTMLVerticalContainerWidget(BaseModuleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_html_vertical_container.html"


class MailedPlainVerticalContainerWidget(BaseModuleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_plain_vertical_container.html"
