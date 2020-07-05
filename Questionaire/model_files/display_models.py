from django.db import models

from Questionaire.model_files.base_models import Question
from PageDisplay.models import Page


class InquiryPage(models.Model):
    """ The display portion of the """
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=256)
    position = models.PositiveIntegerField(unique=True)
    questions = models.ManyToManyField(Question)
    display = models.OneToOneField(Page)

    # Requirements for questions to be answered
    include_on = models.ManyToManyField(Question, related_name="include_questions", blank=True)
    exclude_on = models.ManyToManyField(Question, related_name="exclude_questions", blank=True)
    auto_process = models.BooleanField(default=False)
