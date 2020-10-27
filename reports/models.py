from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify
from django.conf import settings

from Questionaire.models import Technology
from PageDisplay.models import Page

# Import the modules and containers
from .renderers import ReportSinglePageRenderer, ReportMultiPageRenderer


class Report(models.Model):
    report_name = models.CharField(max_length=128, unique=True)
    file_name = models.CharField(max_length=128)
    slug = models.SlugField(editable=False, blank=True, max_length=128, unique=True)
    description = models.TextField(default="", blank=True, null=True)
    promotion_text = models.TextField(blank=True, null=True, verbose_name="Text displayed near download option")
    is_live = models.BooleanField(default=False)
    last_edited = models.DateTimeField(auto_now=True)

    def save(self, **kwargs):
        self.slug = slugify(self.report_name)
        super(Report, self).save(**kwargs)

    def get_pages(self):
        return ReportPage.objects.filter(
            reportpagelink__report=self,
        ).order_by(
            'reportpagelink__page_number'
        ).all()


def upload_layout_path(instance, filename):
    # Throws these files in their seperate report folder
    return 'reports/{id}/layout_templates/{file_name}'.format(id=instance.report.id, file_name=filename)


class PageLayout(models.Model):
    """ Class that contains a visual layout for a certain page """
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    slug = models.SlugField(editable=False, blank=True, max_length=128, unique=True)
    description = models.CharField(max_length=512, null=True, blank=True)
    template = models.FileField(upload_to=upload_layout_path, blank=True)
    margins = models.CharField(max_length=64, default="20mm 20mm 20mm 20mm")

    allowed_template_extensions = ('html', 'txt')

    @property
    def template_content(self):
        """ Returns the template content"""
        self.template.open(mode='rt')
        file_content = self.template.read()
        self.template.close()
        return file_content

    def clean(self):
        if self.template:
            if not self.template.name.lower().endswith(self.allowed_template_extensions):
                raise ValidationError(
                    f"The template file should be of any of the following types: {self.allowed_template_extensions}"
                )

    def save(self, **kwargs):
        self.slug = slugify(self.name)

        if not self.template:
            file_name = f'{self.slug}_template.html'
            file_path = settings.MEDIA_ROOT + upload_layout_path(self, file_name)

            self.template.save(file_name, ContentFile(''))

        super(PageLayout, self).save(**kwargs)

    def __str__(self):
        return self.name


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
        sizes = self.get_paper_sizes_mm()
        sizes['wdith'] = str(sizes['width'])+"mm"
        sizes['height'] = str(sizes['height'])+"mm"
        return sizes

    def get_paper_sizes_mm(self):
        """ Returns the value of the paper size in mm """
        if self.size == 'A3':
            sizes = (297, 420)
        if self.size == 'A4':
            sizes = (210, 297.2)
        if self.size == 'A5':
            sizes = (148, 210)

        if self.orientation:
            return {'width': sizes[0], 'height': sizes[1]}
        return {'width': sizes[1], 'height': sizes[0]}


class ReportPage(Page):
    # General options
    description = models.TextField()
    layout = models.ForeignKey(PageLayout, on_delete=models.SET_NULL, null=True)

    TECHS_ADVISED = 11
    TECHS_DENIED = 12
    TECHS_UNKNOWN = 13

    multi_type = models.IntegerField(
        choices=[
            (TECHS_ADVISED, 'Advised techs'),
            (TECHS_DENIED, 'Not advised techs'),
            (TECHS_UNKNOWN, 'No advise techs')
        ],
        blank=True,
        null=True,
        default=None,
    )

    # Display options
    has_header_footer = models.BooleanField(verbose_name="Has a header or footer", default=True)

    option_fields = ['name', 'description', 'has_header_footer']
    renderer = ReportSinglePageRenderer



    def get_as_child(self):
        # There is only a proxy child that is the case when type is not None
        if self.multi_type is None:
            return ReportPageSingle.objects.get(id=self.id)
        else:
            return ReportPageMultiGenerated.objects.get(id=self.id)

    def is_valid(self, inquiry):
        """ Tests whether this page is valid for the given inquiry """
        return True

    def get_num_plotted_pages(self):
        return 1


class ReportPageManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(multi_type__isnull=True)


class ReportPageSingle(ReportPage):
    """ Represents a report page that renders a single page """
    objects = ReportPageManager()

    class Meta:
        proxy = True


class ReportPageMultiManager(models.Manager):
    """ Represents a report page that contains multiple items of a queryset """

    def get_queryset(self):
        return super().get_queryset().filter(multi_type__isnull=False)


class ReportPageMultiGenerated(ReportPage):

    objects = ReportPageMultiManager()
    renderer = ReportMultiPageRenderer

    class Meta:
        proxy = True


class ReportPageLink(models.Model):
    """ Symbolises the link of a page in a report """
    report = models.ForeignKey(Report, on_delete=models.PROTECT)
    page = models.OneToOneField(ReportPage, on_delete=models.CASCADE)
    page_number = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.report} - {self.page}'


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



