from django.db import models

# Create your models here.


class Question(models.Model):
    """
    A model for a question, can be of multiple types
    """

    name = models.SlugField(max_length=10)
    description = models.CharField(max_length=256)
    question_text = models.CharField(max_length=64)

    # Define the question types
    QUESTION_TYPE_OPTIONS = (
        (0, 'Open question'),
        (1, 'Integer question'),
        (2, 'Double question'),
        (3, 'Choice question'),
    )
    question_type = models.PositiveIntegerField(choices=QUESTION_TYPE_OPTIONS)
    validators = models.TextField(blank=True, null=True, default="{}")

    def __str__(self):
        return self.name


class Page(models.Model):
    """
    A page containing multiple questions
    """
    name = models.CharField(max_length=50)
    position = models.PositiveIntegerField()
    questions = models.ManyToManyField(Question, through='PageEntry',
                                       through_fields=('page', 'question'))

    def meets_requirements(self, inquiry):
        for requirement in self.page_requirements_set:
            if not requirement.is_met(inquiry):
                return False
        return True

    def __str__(self):
        return "{0}: {1}".format(self.position, self.name)

    def is_valid_for_inquiry(self, inquiry):

        for requirement in self.pagerequirement_set.all():
            if not requirement.is_met_for_inquiry(inquiry):
                return False
        return True


class PageEntry(models.Model):
    """
    A model detailing the questions that are on a page in a given order
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=999)
    required = models.BooleanField(default=False)

    unique_together = ("page", "question")

    def __str__(self):
        return "{page} - {pos}: {q}".format(page=self.page, q = self.question, pos = self.position)


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=64)
    value = models.IntegerField()

    def __str__(self):
        return "{question}: {answer}".format(question=self.question.name, answer=self.answer)


class Inquiry(models.Model):
    """
    Combines the result of a single question set added by the user
    """
    current_page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL)
    # Todo: Enter unique address information

    def set_current_page(self, page):
        self.current_page = page
        self.save()

    def get_url(self):
        from django.shortcuts import reverse
        return reverse('q_page', kwargs={'inquiry': self.id, 'page': self.current_page.id})


class InquiryQuestionAnswer(models.Model):
    """
    Contains the answer for a single question in the enquiry
    """
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=256)
    processed = models.BooleanField(default=False)
    processed_answer = models.ForeignKey(AnswerOption, null=True, blank=True, on_delete=models.SET_NULL)

    unique_together = ("inquiry", "question")

    def __str__(self):
        return "{0} {1}: {2}".format(self.question.name, self.inquiry.id, self.answer)


class Technology(models.Model):
    name = models.CharField(max_length=32)

    usefulness_start_value = models.DecimalField(default=0.5, decimal_places=2, max_digits=5)
    usefulness_threshold_approve = models.DecimalField(default=1, decimal_places=2, max_digits=5)
    usefulness_threshold_deny = models.DecimalField(default=0, decimal_places=2, max_digits=5)

    importance_start_value = models.DecimalField(default=0.5, decimal_places=2, max_digits=5)
    importance_threshold_approve = models.DecimalField(default=1, decimal_places=2, max_digits=5)
    importance_threshold_deny = models.DecimalField(default=0, decimal_places=2, max_digits=5)

    short_text = models.CharField(max_length=256)
    long_text = models.TextField()

    def __str__(self):
        return self.name


class TechnologyScore(models.Model):
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE)
    usefulness_score = models.DecimalField(decimal_places=2, max_digits=5)
    importance_score = models.DecimalField(decimal_places=2, max_digits=5)

    def get_useful_state(self):
        if self.usefulness_score >= self.technology.usefulness_threshold_approve:
            return "Beneficial"
        elif self.usefulness_score > self.technology.usefulness_threshold_deny:
            return ""
        else:
            return "Not needed"

    def get_importance_state(self):
        if self.importance_score >= self.technology.importance_threshold_approve:
            return "Important"
        elif self.importance_score > self.technology.importance_threshold_deny:
            return ""
        else:
            return "Not important"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.id is None:
            self.usefulness_score = self.technology.usefulness_start_value
            self.importance_score = self.technology.importance_start_value

    def __str__(self):
        return "{inquiry}: {technology}".format(inquiry=self.inquiry.id, technology=self.technology)


class AnswerScoring(models.Model):
    answer_option = models.ForeignKey(AnswerOption, on_delete=models.CASCADE)
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)
    usefulness_change = models.DecimalField(decimal_places=2, max_digits=5)
    importance_change = models.DecimalField(decimal_places=2, max_digits=5)


class StoredValueDeclaration(models.Model):
    name = models.SlugField(max_length=16)
    start_value = models.DecimalField(default=0, decimal_places=2, max_digits=5)


class StoredInquiryValue(models.Model):
    value_info = models.ForeignKey(StoredValueDeclaration, on_delete=models.CASCADE)
    value = models.DecimalField(decimal_places=2, max_digits=8)
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE)


class PageRequirement(models.Model):
    """
    Illustrates a requirement for the page to be shown
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    score = models.DecimalField(decimal_places=2, max_digits=5)
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
        if self.pagerequirementtechusefulness:
            return self.pagerequirementtechusefulness.is_met_for_inquiry(inquiry)
        elif self.pagerequirementtechimportance:
            return self.pagerequirementtechimportance.is_met_for_inquiry(inquiry)
        else:
            return True

    def is_met(self, value):
        if self.comparison == 0:
            return value > self.score
        elif self.comparison == 1:
            return value >= self.score
        elif self.comparison == 2:
            return value == self.score
        elif self.comparison == 3:
            return value <= self.score
        elif self.comparison == 4:
            return value < self.score
        else:
            raise RuntimeError("Comparison options resulted in unset option")


class PageRequirementTechUsefulness(PageRequirement):
    """
    Illustrates a requirement for the page to be shown
    """
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)

    def is_met_for_inquiry(self, inquiry):
        tech_score = TechnologyScore.objects.get_or_create(technology=self.technology, inquiry=inquiry)[0]
        return self.is_met(tech_score.usefulness_score)


class PageRequirementTechImportance(PageRequirement):
    """
    Illustrates a requirement for the page to be shown
    """
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)

    def is_met_for_inquiry(self, inquiry):
        tech_score = TechnologyScore.objects.get_or_create(technology=self.technology, inquiry=inquiry)[0]
        return self.is_met(tech_score.importance_score)


class PageRequirementStoredValue(PageRequirement):
    """
    Illustrates a requirement for the page to be shown
    """
    value_info = models.ForeignKey(StoredValueDeclaration, on_delete=models.CASCADE)

    def is_met_for_inquiry(self, inquiry):
        value = StoredInquiryValue.objects.get_or_create(value_info=self.value_info, inquiry=inquiry)[0]
        return self.is_met(value.value)