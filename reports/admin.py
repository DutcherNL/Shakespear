from django.contrib import admin

from .models import Report, Page, PageCriteria

# Register your models here.

admin.site.register(Report)
admin.site.register(Page)
admin.site.register(PageCriteria)