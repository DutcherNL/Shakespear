from django.db import models

from Questionaire.models import Question


class QuestionFilter(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    use_for_tech_analysis = models.BooleanField(default=False)
    use_for_progress_analysis = models.BooleanField(default=False)
