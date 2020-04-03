from django.db import models
from django.shortcuts import reverse
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import re


class DataTable(models.Model):
    """ Contains an overall code declaration """
    name = models.CharField(max_length=32)
    slug = models.SlugField(editable=False)
    description = models.CharField(max_length=255)

    is_active = models.BooleanField(default=False)

    def save(self, **kwargs):
        self.slug = slugify(self.name)
        return super(DataTable, self).save(**kwargs)

    def get_absolute_url(self):
        return reverse('setup:local_data_storage:data_table_info', kwargs={'table_slug': self.slug})

    def __str__(self):
        return self.name


class DataColumn(models.Model):
    """ Content identified with a given code in accordance to the code declaration """
    table = models.ForeignKey(DataTable, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    slug = models.SlugField()

    def save(self, **kwargs):
        self.slug = slugify(self.name)
        return super(DataColumn, self).save(**kwargs)




