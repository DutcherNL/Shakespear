from django.db import models

from PageDisplay.models import BaseModule, BasicModuleMixin
from PageDisplay.module_registry import registry

from .widgets import DownloadFileWidget


class DownloadFileModule(BasicModuleMixin, BaseModule):
    _type_id = 13
    verbose = "Download file"
    widget = DownloadFileWidget

    file = models.FileField(blank=True, null=True)
    description = models.CharField(max_length=512)


registry.register(DownloadFileModule)
