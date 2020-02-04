from django.db import models
from django.utils.text import slugify

from Questionaire.models import Technology
from PageDisplay.models import Page

# Import the modules and containers
from .modules.containers import *


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


class ReportPage(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    report = models.ForeignKey(Report, on_delete=models.PROTECT)
    page_number = models.PositiveIntegerField(default=1)
    last_edited = models.DateTimeField(auto_now=True)
    display_page = models.ForeignKey(Page, on_delete=models.PROTECT, blank=True, null=True)

    def is_valid(self, inquiry):
        """ Tests whether this page is valid for the given inquiry """

    def render(self):
        if self.layout:
            return self.layout.render()
        return "No layout defined for {0}".format(self.name)

    def save(self, **kwargs):
        if self.display_page is None:
            page = Page(layout=A4_PageContainer, name=self.name)
            page.save()
            self.display_page = page
        super(ReportPage, self).save(**kwargs)


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



