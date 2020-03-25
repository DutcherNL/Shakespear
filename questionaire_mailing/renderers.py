from PageDisplay.renderers import BasePageRenderer


class MailRenderer(BasePageRenderer):
    template_name = "questionaire_mailing/mails/base.html"