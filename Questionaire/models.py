from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.urls import reverse

from string import Formatter

from DataStorage.models import *
from PageDisplay.models import Information
# Create your models here.


class Question(models.Model):

    """
    A model for a question, can be of multiple types
    """

    name = models.SlugField(max_length=10)
    description = models.CharField(max_length=256)
    question_text = models.CharField(max_length=64)
    help_text = models.CharField(max_length=255, default="", blank=True, null=True)

    # Define the question types
    QUESTION_TYPE_OPTIONS = (
        (0, 'Open question'),
        (1, 'Integer question'),
        (2, 'Double question'),
        (3, 'Choice question'),
    )
    question_type = models.PositiveIntegerField(choices=QUESTION_TYPE_OPTIONS)
    options = models.TextField(blank=True, null=True, default="{}")

    def __str__(self):
        return self.name


class Page(models.Model):
    """
    A page containing multiple questions
    """
    name = models.CharField(max_length=50)
    position = models.PositiveIntegerField(unique=True)
    questions = models.ManyToManyField(Question, through='PageEntryQuestion',
                                       through_fields=('page', 'question'))
    auto_process = models.BooleanField(default=False)

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
    position = models.PositiveIntegerField(default=999)
    # Define the entry types, saved here for database use optimisation
    ENTRY_TYPE_OPTIONS = (
        (1, 'General information'),
        (2, 'Question'),
    )
    entry_type = models.PositiveIntegerField(choices=ENTRY_TYPE_OPTIONS)

    def __str__(self):
        i = self.ENTRY_TYPE_OPTIONS[self.entry_type-1][1]

        return "{page} - {pos}: {q}".format(page=self.page, q = i, pos = self.position)


class PageEntryText(PageEntry):
    """
    Represents a textual entry on a page
    """
    text = models.TextField(default="")

    def __init__(self, *args, **kwargs):
        super(PageEntryText, self).__init__(*args, **kwargs)
        self.entry_type = 1


class PageEntryQuestion(PageEntry):
    """
    Represents a question entry on a page
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    required = models.BooleanField(default=False)

    unique_together = ("page", "question")

    def __init__(self, *args, **kwargs):
        super(PageEntryQuestion, self).__init__(*args, **kwargs)
        self.entry_type = 2


class AnswerOption(models.Model):
    """
    An option for a multiple choice answer
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=64)
    value = models.IntegerField()
    image = models.ImageField(null=True, blank=True)

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
        if self.current_page is None:
            first_page = Page.objects.order_by('position').first()
            return reverse('q_page', kwargs={'inquiry': self.id, 'page': first_page.id})
        else:
            return reverse('q_page', kwargs={'inquiry': self.id, 'page': self.current_page.id})

    # DO NOT ADJUST THE FOLLOWING PARAMETERS AFTER DEPLOYMENT!
    length = 6
    allowed_chars = 'QZXSWDCVFRTGBYHNMJKLP'
    steps = 2766917
    # DO NOT ADJUST THE ABOVE PARAMETERS AFTER DEPLOYMENT!

    @classmethod
    def get_inquiry_code_from_model(cls, model):
        """
        Get the lettercode for this inquiry object
        :return: Returns the lettercode for the given inquiry object
        """
        # New value is the key multiplied by the steps mod the total number of possibilities
        value = (model.pk * cls.steps) % (len(cls.allowed_chars) ** cls.length)
        string = ''

        # Translate the reformed number to its letterform
        for i in range(cls.length-1, 0 -1, -1):
            base = len(cls.allowed_chars) ** i

            # Compute the position of the character (devide by base rounded down)
            char_pos = int(value / base)
            # Add the new character to the string
            string += cls.allowed_chars[char_pos]
            # Remove the processed value from the string
            value -= (base * char_pos)

        return string

    def get_inquiry_code(self):
        return Inquiry.get_inquiry_code_from_model(self)

    def get_rev_key(self):
        return Inquiry.get_inquiry_model_from_code(self.get_inquiry_code_from_model(self)).id

    @classmethod
    def get_inquiry_model_from_code(cls, code):
        """
        Retrieves the inquiry model based on a given letter-code
        :param code: The 6-letter code
        :return: The inquiry-model TODO: return inquiry model instead of pk number
        """

        def egcd(a, b):
            """
            Extended Euclidean Algorithm
            :param a: Int number 1
            :param b: Int number 2
            :return: the greatest common division (gcd) and the x and y values according to ax +by = gcd
            """
            x,y, u,v = 0,1, 1,0
            while a != 0:
                q, r = b//a, b%a
                m, n = x-u*q, y-v*q
                b,a, x,y, u,v = a,r, u,v, m,n
            gcd = b
            return gcd, x, y

        # Define base variables
        value = 0
        max_combos = (len(cls.allowed_chars) ** cls.length)

        # Translate the code to the reformed number
        for i in range(0, len(code)):
            char_pos = cls.allowed_chars.find(code[i])

            if char_pos == -1:
                raise ValidationError("Character was not the possible characters")
            else:
                value += char_pos * (len(cls.allowed_chars) ** (cls.length - i - 1))

        # Recompute the reformed number to its original number
        gcd, x, y = egcd(cls.steps, max_combos)
        id = (value * x) % max_combos

        # Return the result
        return cls.objects.get(id=id)


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

    def get_readable_answer(self):
        """
        Returns a human readable answer, as given
        :return: a human readable string
        """
        if self.question.question_type == 3:
            if self.answer == "0":
                # The answer has not been given
                return "not given"
            return AnswerOption.objects.get(question=self.question, value=self.answer).answer

        return self.answer


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
    score = models.DecimalField(decimal_places=2, max_digits=5)

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
            # Todo: get the value of the given answer
            pass

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


class ExternalQuestionSource(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    code_type = models.ForeignKey(StoredDataCodeDeclaration, on_delete=models.CASCADE)
    content_type = models.ForeignKey(StoredDataDeclaration, on_delete=models.CASCADE)
    code_source = models.CharField(max_length=256)

    def get_code(self, inquiry=None):
        formatter = Formatter()
        iter_obj = formatter.parse(self.code_source)
        keys = []
        for literal, key, format, conversion in iter_obj:
            keys.append(key)

        format_dict = {}

        try:
            for key in keys:
                if key is None:
                    continue

                if key.startswith('q_'):
                    iqa_obj = InquiryQuestionAnswer.objects.get(question__name=key[2:], inquiry=inquiry)
                    format_dict[key] = iqa_obj.get_readable_answer()
                elif key.startswith('v_'):
                    score_obj = Score.objects.get(declaration__name=key[2:], inquiry=inquiry)
                    format_dict[key] = score_obj.score

            return self.code_source.format(**format_dict)
        except ObjectDoesNotExist:
            return None

    def get_content(self, inquiry=None):
        code = self.get_code(inquiry=inquiry)
        if code is None:
            return None

        try:
            return StoredDataContent.objects.get(code__identification_code=code,
                                                 code__code_type=self.code_type,
                                                 data_declaration=self.content_type).content
        except StoredDataContent.DoesNotExist:
            return None





