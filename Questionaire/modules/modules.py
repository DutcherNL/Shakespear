from django.db import models

from PageDisplay.models import BaseModule
from PageDisplay.module_registry import registry

from Questionaire.models import Technology
from Questionaire.modules.widgets import TechScoreWidget


class TechScoreModule(BaseModule):
    """ A module that displays the scores of a technology """
    type_id = 11
    verbose = "TechScore"
    widget = TechScoreWidget

    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)


registry.register(TechScoreModule)
