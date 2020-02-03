from django.contrib import admin

from .models import Report, ReportPage, PageCriteria

# Register your models here.

admin.site.register(Report)
admin.site.register(ReportPage)
admin.site.register(PageCriteria)
