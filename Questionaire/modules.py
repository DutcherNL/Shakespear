from django.db import models

from PageDisplay.models import BaseModule
from PageDisplay.module_registry import registry

from .models import Technology


class TechScoreModule(BaseModule):
    """ A module that displays the scores of a technology """
    type_id = 11
    verbose = "TechScore"
    template_name = "inquiry_pages/inquiry_snippets/snippet_tech_group_info.html"

    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)


registry.register(TechScoreModule)