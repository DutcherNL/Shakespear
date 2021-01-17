from django.db import models
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from PageDisplay.models import BaseModule, BasicModuleMixin
from PageDisplay.module_registry import registry

from .widgets import DownloadFileWidget, ExternalURLWidget


class DownloadFileModule(BasicModuleMixin, BaseModule):
    _type_id = 13
    verbose = "Download file"
    widget = DownloadFileWidget

    file = models.FileField(blank=True, null=True)
    description = models.CharField(max_length=512)


def validate_test(value):
    raise ValidationError("Validation halted")


class ExternalURLModule(BasicModuleMixin, BaseModule):
    _type_id = 22
    verbose = "Drop URL"
    widget = ExternalURLWidget

    url = models.CharField(max_length=128, validators=[URLValidator()])
    guide_text = models.CharField(max_length=128, default=_('View online'))


registry.register(DownloadFileModule)
registry.register(ExternalURLModule)
