import ast
from django.db import models
from django.utils import timezone

from Questionaire.processors.code_translation import inquiry_6encoder
from Questionaire.processors import question_processors


__all__ = ['Question', 'Page', 'PageEntry', 'PageEntryText', 'PageEntryQuestion', 'AnswerOption',
           'Inquiry', 'Inquirer', 'InquiryQuestionAnswer']


class Question(models.Model):
    """ A model for a question, can be of multiple types """

    name = models.SlugField(max_length=25, unique=True)
    description = models.CharField(max_length=256)
    question_text = models.CharField(max_length=128)
    help_text = models.CharField(max_length=255, default="", blank=True, null=True)

    TYPE_OPEN = 0
    TYPE_INT = 1
    TYPE_DOUBLE = 2
    TYPE_CHOICE = 3

    # Define the question types
    QUESTION_TYPE_OPTIONS = (
        (TYPE_OPEN, 'Open question'),
        (TYPE_INT, 'Integer question'),
        (TYPE_DOUBLE, 'Double question'),
        (TYPE_CHOICE, 'Choice question'),
    )
    question_type = models.PositiveIntegerField(choices=QUESTION_TYPE_OPTIONS)
    options = models.TextField(blank=True, null=True, default="{}")

    def __str__(self):
        return self.name

    @property
    def options_dict(self):
        """ Returns a dictionary of all defined options for this question"""
        return ast.literal_eval(self.options)

    def question_is_answered(self, inquiry):
        """ Checks if the quesiton has an answer for a given inquiry
        :param inquiry: Inquiry object
        :return: Boolean if question has an answer in inquiry
        """
        try:
            iqa = InquiryQuestionAnswer.objects.get(inquiry=inquiry, question=self)
            return iqa.processed
        except InquiryQuestionAnswer.DoesNotExist:
            return False

    def answer_for_inquiry(self, inquiry, answer_value, process=True):
        """
        Creates or updates an answer given to this question
        :param inquiry: The inquiry the answer is part of
        :param answer_value: The value of the answer
        :param process: Whether the answer option should be processed/ searched
        :return: The InquiryQuestionAnswer object updated
        """
        iqa = InquiryQuestionAnswer.objects.get_or_create(inquiry=inquiry, question=self)[0]
        iqa.answer = answer_value
        if process:
            iqa.get_answer_option(update_on_obj=True)
        iqa.save()
        return iqa


class Page(models.Model):
    """ A page containing multiple questions """
    name = models.CharField(max_length=50)
    position = models.PositiveIntegerField(unique=True)
    questions = models.ManyToManyField(Question, through='PageEntryQuestion',
                                       through_fields=('page', 'question'))
    # Requirements for questions to be answered
    include_on = models.ManyToManyField(Question, related_name="include_questions", blank=True)
    exclude_on = models.ManyToManyField(Question, related_name="exclude_questions", blank=True)
    auto_process = models.BooleanField(default=False)

    def __str__(self):
        return "{0}: {1}".format(self.position, self.name)

    def is_valid_for_inquiry(self, inquiry):
        """
        Checks if the page should be displayed and computed for the given inquiry

        A page has a pagerequirement for tracked scores
        A page can require to have certain questions to be answered
        A page can require certain questions not to have been answered

        :param inquiry: The inquiry object that the page needs to be displayed for
        :return: Boolean if the page is a valid page to process
        """
        # Check if the requirements are met
        for requirement in self.pagerequirement_set.all():
            if not requirement.is_met_for_inquiry(inquiry):
                return False
        # Check if the required questions are answered
        for question in self.include_on.all():
            if not question.question_is_answered(inquiry):
                return False
        # Check if the forbidden questions are not answered
        for question in self.exclude_on.all():
            if question.question_is_answered(inquiry):
                return False

        return True


class PageEntry(models.Model):
    """ A model detailing the content that is on a page in a given order """
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=999)
    # Define the entry types, saved here for database use optimisation
    ENTRY_TYPE_OPTIONS = (
        (1, 'General information'),
        (2, 'Question'),
    )
    entry_type = models.PositiveIntegerField(choices=ENTRY_TYPE_OPTIONS, blank=True)

    def __str__(self):
        i = self.ENTRY_TYPE_OPTIONS[self.entry_type-1][1]

        return "{page} - {pos}: {q}".format(page=self.page, q = i, pos = self.position)

    def save(self, *args, **kwargs):
        # Set the entry_type (defining the model type)
        self.entry_type = self._entry_type
        super(PageEntry, self).save(*args, **kwargs)


class PageEntryText(PageEntry):
    """ Represents a textual entry on a page """
    text = models.TextField(default="")

    _entry_type = 1


class PageEntryQuestion(PageEntry):
    """ Represents a question entry on a page """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    required = models.BooleanField(default=False)

    unique_together = ("page", "question")

    _entry_type = 2


class AnswerOption(models.Model):
    """ An option for a multiple choice answer """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=64)
    context_code = models.CharField(blank=True, null=True, max_length=256)
    value = models.IntegerField()
    image = models.ImageField(null=True, blank=True)

    def __str__(self):
        return "{question}: {answer}".format(question=self.question.name, answer=self.answer)

    def forward_for_inquiry(self, inquiry):
        """ Executes a forward processing movement for all adjustments in the inquiry"""
        # Import the Score class (done here as previously it wasn't processed yet
        from Questionaire.model_files.tech_scoring_models import Score

        # Loop over all adjustments and adjust them
        for adjustment in self.answerscoring_set.all():
            score_obj = Score.objects.get_or_create(declaration=adjustment.declaration, inquiry=inquiry)[0]
            adjustment.adjust_score(score_obj)
            score_obj.save()

    def backward_for_inquiry(self, inquiry):
        # Import the Score class (done here as previously it wasn't processed yet
        from Questionaire.model_files.tech_scoring_models import Score

        # Loop over all adjustments and adjust them
        for adjustment in self.answerscoring_set.all():
            # Revert all the scores
            score_obj = Score.objects.get_or_create(declaration=adjustment.declaration, inquiry=inquiry)[0]
            adjustment.adjust_score(score_obj, revert=True)
            score_obj.save()


class Inquiry(models.Model):
    """ Combines the result of a single question set added by the user """
    current_page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL)
    is_complete = models.BooleanField(default=False)
    completed_on = models.DateTimeField(null=True, blank=True)
    # Todo, addition and test case for completed on tracking
    created_on = models.DateTimeField(auto_now_add=True)
    last_visited = models.DateTimeField(auto_now=True)
    inquirer = models.ForeignKey('Inquirer', on_delete=models.CASCADE)

    def set_current_page(self, page):
        self.current_page = page
        self.save()

    def get_absolute_url(self):
        from django.shortcuts import reverse
        if self.current_page is None:
            if self.is_complete:
                return reverse('results_display')

            first_page = Page.objects.order_by('position').first()
            return reverse('debug_q_page', kwargs={'inquiry': self.id, 'page': first_page.id})
        else:
            return reverse('debug_q_page', kwargs={'inquiry': self.id, 'page': self.current_page.id})

    def complete(self):
        """ A script that is called when the questionaire is completed """
        self.is_complete = True
        self.completed_on = timezone.now()
        self.current_page = None
        self.save()

    def reset(self):
        """ Resets the inquiry data, it maintains all answers, but removes all scores """
        # Remove all score objects
        self.score_set.all().delete()

        # Clear all processed states
        for answer in self.inquiryquestionanswer_set.all():
            answer.processed = False
            answer.processed_answer = None
            answer.save()

        # Adjust own state
        self.is_complete = False
        self.current_page = Page.objects.order_by('position').first()
        self.save()

    @property
    def get_owner(self):
        return self.inquirer.get_email()


class Inquirer(models.Model):
    """ Contains information of a single user filling in queries """
    email = models.EmailField(blank=True, null=True)
    active_inquiry = models.ForeignKey(Inquiry, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_on_set')
    created_on = models.DateTimeField(auto_now_add=True)

    def get_email(self):
        return self.email or "-Not given-"

    @classmethod
    def get_inquiry_code_from_model(cls, model):
        """
        Get the lettercode for this inquiry object
        :return: Returns the lettercode for the given inquiry object
        """
        inquiry_6encoder.get_code_from_id(model.id)

    def get_inquiry_code(self):
        return inquiry_6encoder.get_code_from_id(self.id)

    @classmethod
    def get_inquiry_model_from_code(cls, code):
        """
        Retrieves the inquiry model based on a given letter-code
        :param code: The 6-letter code
        :return: The inquiry-model
        """
        # Uncode the code
        id_value = inquiry_6encoder.get_id_from_code(code)

        # Return the result
        return cls.objects.get(id=id_value)


class InquiryQuestionAnswer(models.Model):
    """ Contains the answer for a single question in the enquiry """
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=256, blank=True, null=True)

    # Content to define whether the answer has been processed and as what
    processed = models.BooleanField(default=False)
    processed_answer = models.ForeignKey(AnswerOption, null=True, blank=True, on_delete=models.SET_NULL)

    unique_together = ("inquiry", "question")

    def __str__(self):
        return "{0} {1}: {2}".format(self.question.name, self.inquiry.id, self.answer)

    def get_readable_answer(self, with_answer_code=False):
        """ Returns a human readable answer, as given

        :return: a human readable string
        """
        if with_answer_code:
            if self.processed_answer:
                return self.processed_answer.context_code
            return ""

        if self.question.question_type == 3:
            if self.answer == "0":
                # The answer has not been given
                return "not given"
            return AnswerOption.objects.get(question=self.question, value=self.answer).answer

        return self.answer

    def forward(self):
        """
        Computes the processed answer and adjust the scoring accordingly
        :return:
        """
        # Answer is already processed and should not be processed again
        if self.processed:
            return

        if self.processed_answer is not None:
            self.processed_answer.forward_for_inquiry(self.inquiry)
            self.processed = True
            self.save()

    def backward(self):
        """ Reverts the processed answer by adjusting the scoring accordingly """
        # If the current answer is not processed, it is useless to undo the process
        if not self.processed:
            return

        if self.processed_answer is not None:
            self.processed_answer.backward_for_inquiry(self.inquiry)
            # Set the answer as unprocessed
            self.processed = False
            self.save()

    def get_answer_option(self, update_on_obj=False):
        """
        Attempts to find the relevant answer option
        :param update_on_obj: Whether the solution should replace processed_answer
        :return: The selected answer option
        """
        answer_option = question_processors.get_answer_option_from_answer(self)
        if update_on_obj:
            self.processed_answer = answer_option
        return answer_option

