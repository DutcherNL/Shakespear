from django.db import models

from Questionaire.models import Question


class QuestionFilter(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)