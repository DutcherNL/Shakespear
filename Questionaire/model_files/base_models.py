from django.db import models
from django.core.exceptions import ValidationError


class Question(models.Model):
    """ A model for a question, can be of multiple types """

    name = models.SlugField(max_length=10)
    description = models.CharField(max_length=256)
    question_text = models.CharField(max_length=128)
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

    def question_is_answered(self, inquiry):
        """ Checks if the quesiton has an answer for a given inquiry
        :param inquiry: Inquiry object
        :return: Boolean if question has an answer in inquiry
        """
        try:
            iqa = InquiryQuestionAnswer.objects.get(inquiry=inquiry, question=self)
            if iqa.processed_answer is None:
                return False
            else:
                return True
        except InquiryQuestionAnswer.DoesNotExist:
            return False


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


class Inquiry(models.Model):
    """ Combines the result of a single question set added by the user """
    current_page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL)
    is_complete = models.BooleanField(default=False)

    def set_current_page(self, page):
        self.current_page = page
        self.save()

    def get_url(self):
        from django.shortcuts import reverse
        if self.current_page is None:
            if self.is_complete:
                return reverse('results_display')


            first_page = Page.objects.order_by('position').first()
            return reverse('debug_q_page', kwargs={'inquiry': self.id, 'page': first_page.id})
        else:
            return reverse('debug_q_page', kwargs={'inquiry': self.id, 'page': self.current_page.id})

    def complete(self):
        self.is_complete = True
        self.current_page = None
        self.save()


class Inquirer(models.Model):
    """ Contains information of a single user filling in queries """
    email = models.EmailField(blank=True, null=True)
    active_inquiry = models.ForeignKey(Inquiry, on_delete=models.SET_NULL, null=True, blank=True)

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
        return Inquirer.get_inquiry_code_from_model(self)

    def get_rev_key(self):
        return Inquirer.get_inquiry_model_from_code(self.get_inquiry_code_from_model(self)).id

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
    """ Contains the answer for a single question in the enquiry """
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=256)

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
            return None

        if self.question.question_type == 3:
            if self.answer == "0":
                # The answer has not been given
                return "not given"
            return AnswerOption.objects.get(question=self.question, value=self.answer).answer

        return self.answer


