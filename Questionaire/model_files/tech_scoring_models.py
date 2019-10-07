from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.urls import reverse

from string import Formatter
from decimal import *
from PageDisplay.models import Information

from .base_models import Inquiry, AnswerOption, InquiryQuestionAnswer, Page


class ScoringDeclaration(models.Model):
    """
    Declares a score that should be tracked
    """
    name = models.SlugField(max_length=32)
    display_name = models.CharField(max_length=64, blank=True, null=True)
    description = models.CharField(max_length=256)
    score_start_value = models.DecimalField(default=0.5, decimal_places=2, max_digits=5)

    def __str__(self):
        return self.name


class Technology(models.Model):
    """
    Gives all information related to a technology
    """
    name = models.CharField(max_length=32)
    short_text = models.CharField(max_length=256)
    icon = models.ImageField(blank=True, null=True)
    score_declarations = models.ManyToManyField(ScoringDeclaration,
                                                through='TechScoreLink',
                                                through_fields=('technology', 'score_declaration'))
    information_page = models.ForeignKey(Information, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_score(self, inquiry=None):
        """
        Returns the resulting score for the specefic technology
        :param inquiry: the inquiry model
        :return: 0 is not met, 1 if met, 0.5 if unsure
        """
        score = 1
        for scorelink in self.techscorelink_set.all():
            score = scorelink.get_score(inquiry=inquiry) * score

        return score

    def get_absolute_url(self):
        if self.information_page:
            return reverse('info_page', kwargs={'inf_id': self.information_page.id})
        else:
            return None


class TechScoreLink(models.Model):
    """
    Defines a link between a technology and score declaration and set the thresholds for that declaration
    """
    score_declaration = models.ForeignKey(ScoringDeclaration, on_delete=models.PROTECT)
    technology = models.ForeignKey(Technology, on_delete=models.PROTECT)
    score_threshold_approve = models.DecimalField(default=1, decimal_places=2, max_digits=5)
    score_threshold_deny = models.DecimalField(default=0, decimal_places=2, max_digits=5)

    def get_score(self, inquiry=None):
        """
        Returns the resulting score for the specefic link
        :param inquiry:
        :return: 0 is not met, 1 if met, 0.5 if unsure
        """
        score_obj = Score.objects.get_or_create(inquiry=inquiry, declaration=self.score_declaration)[0]

        if score_obj.score > self.score_threshold_approve:
            return 1
        if score_obj.score < self.score_threshold_deny:
            return 0
        return 0.5


class Score(models.Model):
    """
    Tracks the score of a specific Scoretype for a specific inquiry
    """
    declaration = models.ForeignKey(ScoringDeclaration, on_delete=models.CASCADE)
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE)
    score = models.DecimalField(decimal_places=2, max_digits=7)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.id is None:
            self.score = self.declaration.score_start_value

    def __str__(self):
        return "{scorename}: {inquiry}".format(scorename=self.declaration.name, inquiry=self.inquiry.id)


class AnswerScoring(models.Model):
    """
    Contains information on scores to be altered for a selected answer
    """
    answer_option = models.ForeignKey(AnswerOption, on_delete=models.CASCADE)
    declaration = models.ForeignKey(ScoringDeclaration, on_delete=models.CASCADE)
    score_change_value = models.DecimalField(decimal_places=2, max_digits=5)
    take_answer_value = models.BooleanField(default=False)

    def adjust_score(self, score_obj, revert=False):
        if self.take_answer_value:
            question = self.answer_option.question
            iqa = InquiryQuestionAnswer.objects.get(inquiry=score_obj.inquiry,
                                                    question=question)
            if revert:
                score_obj.score = score_obj.score - Decimal(iqa.answer)
            else:
                score_obj.score = score_obj.score + Decimal(iqa.answer)

        if revert:
            score_obj.score = score_obj.score - self.score_change_value
        else:
            score_obj.score = score_obj.score + self.score_change_value

    def __str__(self):
        return "{0}:{1} - {2}".format(self.answer_option.question.name, self.answer_option.answer, self.declaration.name)


class PageRequirement(models.Model):
    """
    Illustrates a requirement for the page to be shown
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    score_declaration = models.ForeignKey(ScoringDeclaration, on_delete=models.CASCADE)
    threshold = models.DecimalField(decimal_places=2, max_digits=5)
    # Define the question types
    COMPRARISON_OPTIONS = (
        (0, 'Higher'),
        (1, 'Higher or equal'),
        (2, 'Equal'),
        (3, 'Lower or Equal'),
        (4, 'Lower'),
    )
    comparison = models.PositiveIntegerField(choices=COMPRARISON_OPTIONS)

    def is_met_for_inquiry(self, inquiry):
        inquiry_score = Score.objects.get_or_create(declaration=self.score_declaration, inquiry=inquiry)[0].score
        if self.comparison == 0:
            return inquiry_score > self.threshold
        elif self.comparison == 1:
            return inquiry_score >= self.threshold
        elif self.comparison == 2:
            return inquiry_score == self.threshold
        elif self.comparison == 3:
            return inquiry_score <= self.threshold
        elif self.comparison == 4:
            return inquiry_score < self.threshold
        else:
            raise RuntimeError("Comparison options resulted in unset option")


class AnswerScoringNote(models.Model):
    scoring = models.ForeignKey(AnswerScoring, on_delete=models.CASCADE)
    technology = models.ForeignKey(Technology, blank=True, null=True, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True, default="Nothing defined")
    exclude_on = models.ManyToManyField(AnswerOption, related_name="Answer_excludes", blank=True)
    include_on = models.ManyToManyField(AnswerOption, related_name="Answer_includes", blank=True)

    def __str__(self):
        return "{tech}: {answer}".format(tech=self.technology, answer=self.scoring.answer_option)

    def get_prepped_text(self, inquiry=None):
        formatter = Formatter()
        iter_obj = formatter.parse(self.text)
        keys = []
        for literal, key, format, conversion in iter_obj:
            keys.append(key)

        format_dict = {}
        for key in keys:
            if key is None:
                continue

            if key.startswith('q_'):
                iqa_obj = InquiryQuestionAnswer.objects.get(question__name=key[2:], inquiry=inquiry)
                format_dict[key] = iqa_obj.get_readable_answer()
            elif key.startswith('v_'):
                score_obj = Score.objects.get(declaration__name=key[2:], inquiry=inquiry)
                format_dict[key] = score_obj.score

        return self.text.format(**format_dict)
