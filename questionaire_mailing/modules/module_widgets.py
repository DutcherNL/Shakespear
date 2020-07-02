from general import get_absolute_url_path
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

    def get_context_data(self, request=None, **kwargs):
        context = super(InquirerCodeWidgetMixin, self).get_context_data(request=request, **kwargs)

        inquirer = kwargs.get('inquirer', None)

        if inquirer:
            context['inquirer_code'] = inquirer.get_inquiry_code()
        else:
            context['inquirer_code'] = "code onbekend (oeps, foutje)"
        return context


class MailedHTMLInquirerCodeWidget(InquirerCodeWidgetMixin, BaseModuleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_html_inquirer_code.html"


class MailedPlainInquirerCodeWidget(InquirerCodeWidgetMixin, BaseModuleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_plain_inquirer_code.html"


class MailConfirmationWidgetMixin:
    use_from_context = ['inquirer']

    def get_context_data(self, request=None, inquirer=None, **kwargs):
        context = super(MailConfirmationWidgetMixin, self).get_context_data(request=request, **kwargs)

        context['pending_url'] = self.get_pending_url(inquirer)
        context['as_button'] = True

        return context

    def get_pending_url(self, inquirer):
        from inquirer_settings.models import PendingMailVerifyer
        pending_mail = PendingMailVerifyer.objects.filter(
            inquirer=inquirer,
            active=True
        ).first()
        if pending_mail:
            path = pending_mail.get_absolute_url()
            return get_absolute_url_path(path)
        else:
            return None


class MailedHTMLMailConfirmationWidget(MailConfirmationWidgetMixin, BaseModuleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_html_mail_confirmation.html"


class MailedPlainMailConfirmationWidget(MailConfirmationWidgetMixin, BaseModuleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_plain_mail_confirmation.html"


class MailedHTMLVerticalContainerWidget(BaseModuleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_html_vertical_container.html"


class MailedPlainVerticalContainerWidget(BaseModuleWidget):
    template_name = "questionaire_mailing/modules/module_mailed_plain_vertical_container.html"
