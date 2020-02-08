from django.db import models
from django.utils.text import slugify

from Questionaire.models import Technology
from PageDisplay.models import Page

# Import the modules and containers
from .renderers import ReportPageRenderer


class Report(models.Model):
    report_name = models.CharField(max_length=128, unique=True)
    file_name = models.CharField(max_length=128)
    slug = models.SlugField(editable=False, blank=True, max_length=128, unique=True)
    description = models.TextField(default="", blank=True, null=True)
    is_live = models.BooleanField(default=False)
    last_edited = models.DateTimeField(auto_now=True)

    def save(self, **kwargs):
        self.slug = slugify(self.report_name)
        super(Report, self).save(**kwargs)

    def get_pages(self):
        return self.reportpage_set.order_by('page_number').all()


class ReportDisplayOptions(models.Model):
    report = models.OneToOneField(to=Report, on_delete=models.CASCADE, related_name="display_options", editable=False)

    # Paper design
    PAPER_SIZES = [
        ('A3', 'A3 (297 x 420mm)'),
        ('A4', 'A4 (210 x 297mm)'),
        ('A5', 'A5 (148 x 210mm)'),
    ]
    size = models.CharField(max_length=3, choices=PAPER_SIZES, default='A4')
    orientation = models.BooleanField(choices=[
        (True, "Standing"),
        (False, "Rotated")], default=True)

    margins = models.CharField(max_length=256, default="20mm 20mm 20mm 20mm")

    # Report
    header = models.CharField(max_length=256, default="header", null=True, blank=True)
    footer = models.CharField(max_length=256, default="footer", null=True, blank=True)

    @property
    def paper_proportions(self):
        """ Returns a dict of the height and width of the pages in the report"""
        if self.size == 'A3':
            size = ("297mm", "420mm")
        if self.size == 'A4':
            sizes = ("210mm", "297mm")
        if self.size == 'A5':
            sizes = ("148mm", "210mm")

        if self.orientation:
            return {'width': sizes[0], 'height': sizes[1]}
        return {'width': sizes[1], 'height': sizes[0]}


class ReportPage(Page):
    # General options
    description = models.TextField()
    report = models.ForeignKey(Report, on_delete=models.PROTECT)
    page_number = models.PositiveIntegerField(default=1)
    last_edited = models.DateTimeField(auto_now=True)

    # Display options
    has_header_footer = models.BooleanField(verbose_name="Has a header or footer", default=True)

    option_fields = ['name', 'description', 'has_header_footer']
    renderer = ReportPageRenderer

    def __init__(self, *args, **kwargs):
        super(ReportPage, self).__init__(*args, **kwargs)

    def is_valid(self, inquiry):
        """ Tests whether this page is valid for the given inquiry """
        return True


class PageCriteria(models.Model):
    """ Adds the page in the report if a certain criteria is met """
    page = models.ForeignKey(ReportPage, on_delete=models.CASCADE)

    def is_met(self, inquiry):
        return NotImplementedError


class TechnologyPageCriteria(PageCriteria):
    """ Adds a criteria based on the score of a technology """
    technology = models.ForeignKey(Technology, on_delete=models.SET_NULL, null=True)
    _score_options = [
            (Technology.TECH_SUCCESS, 'Succesvol'),
            (Technology.TECH_VARIES, 'Wisselend'),
            (Technology.TECH_FAIL, 'Afgeraden'),
            (Technology.TECH_UNKNOWN, 'Onbekend'),
    ]
    score = models.IntegerField(choices=_score_options)


class LogicPageCriteria(PageCriteria):
    criteria = models.ManyToManyField(PageCriteria, related_name='super_criteria')
    _options = [
        (0, 'OR'),
        (1, 'AND'),
        (2, 'NOR'),
        (3, 'NAND'),
        (4, 'XOR'),
        (5, 'XNOR'),
    ]
    logic = models.IntegerField(choices=_options, default=0)



