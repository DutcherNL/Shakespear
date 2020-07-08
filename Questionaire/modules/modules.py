from django.db import models

from PageDisplay.models import BaseModule, BasicModuleMixin
from PageDisplay.module_registry import registry

from Questionaire.models import Technology, Question
from Questionaire.modules.widgets import *

__all__ = ['QuestionModule', 'TechScoreModule']


class QuestionModule(BasicModuleMixin, BaseModule):
    _type_id = 17
    verbose = "Question"
    widget = QuestionWidget
    exclude_editing_fields = ['question']

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    required = models.BooleanField(default=False)

    def get_fixed_properties(self, *args):
        """ Get fixed properties to display in the fixed properties window """
        return super(QuestionModule, self).get_fixed_properties(
            ('question', self.question),
            *args
        )

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