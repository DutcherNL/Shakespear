from django.db import models

from PageDisplay.models import BaseModule, BasicModuleMixin
from PageDisplay.module_registry import registry

from Questionaire.models import Technology, Question
from Questionaire.modules.widgets import *


class QuestionModule(BasicModuleMixin, BaseModule):
    _type_id = 17
    verbose = "Question"
    widget = QuestionWidget

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    required = models.BooleanField(default=False)


class TechScoreModule(BasicModuleMixin, BaseModule):
    """ A module that displays the scores of a technology """
    # Todo, change this to _type_id, currently its in the database as id 0
    type_id = 101
    verbose = "TechScore"
    widget = TechScoreWidget

    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)
    display_description = models.BooleanField(default=True, verbose_name="Display tech description")
    display_notes = models.BooleanField(default=True, verbose_name="Display scoring notes")
    display_sub_technologies = models.BooleanField(default=False, verbose_name="Display underlying technologies")


registry.register(TechScoreModule)
registry.register(QuestionModule, in_default=False)