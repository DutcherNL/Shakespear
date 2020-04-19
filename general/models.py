from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class BasePageURL(models.Model):
    """ Links a Page object with a given url """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, default="", unique=True, blank=True,
                            help_text="De naam in de url, laat leeg om automatisch te genereren ut de titel")
    description = models.CharField(default="", max_length=128)
    in_footer = models.BooleanField(default=True, verbose_name="Whether the page is linked in the footer")
    footer_order = models.IntegerField(default=0, verbose_name="Order of appearance in the footer")

    page = models.ForeignKey('PageDisplay.Page', on_delete=models.CASCADE, blank=True, editable=False)

    def save(self, **kwargs):
        if self.slug == "":
            self.slug = slugify(self.name)

        if self.id is None:
            from PageDisplay.models import Page
            self.page = Page.objects.create(name=self.name)

        return super(BasePageURL, self).save(**kwargs)

    def get_absolute_url(self):
        return reverse("general:general_pages:view_page", kwargs={'slug': self.slug})

    def __str__(self):
        return self.name

    def delete(self, **kwargs):
        page = self.page
        result = super(BasePageURL, self).delete(**kwargs)
        page.delete()
        return result