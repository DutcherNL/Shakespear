from django.contrib import admin

from .models import Report, ReportPage, PageCriteria
from .modules import containers

# Register your models here.

admin.site.register(Report)
admin.site.register(ReportPage)
admin.site.register(PageCriteria)
admin.site.register(containers.PageContainer)
