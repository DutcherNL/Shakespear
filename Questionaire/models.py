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

    def __str__(self):
        return "{0}: {1}".format(self.position, self.name)


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
    pass


class Inquiry(models.Model):
    """
    Combines the result of a single question set added by the user
    """
    # Todo: Enter unique address information
    pass


class InquiryQuestionAnswer(models.Model):
    """
    Contains the answer for a single question in the enquiry
    """
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=256)
    processed = models.BooleanField(default=False)

    unique_together = ("inquiry", "question")

    def __str__(self):
        return "{0} {1}: {2}".format(self.question.name, self.inquiry.id, self.answer)

