from django.db import models

from PageDisplay.models import BaseModule, BasicModuleMixin
from PageDisplay.module_registry import registry, AlreadyRegistered

from questionaire_mailing.modules import module_widgets


class InquirerCodeModule(BasicModuleMixin, BaseModule):
    _type_id = 312
    verbose = "Inquirer code"
    widget = module_widgets.MailedHTMLInquirerCodeWidget


registry.register(InquirerCodeModule)
