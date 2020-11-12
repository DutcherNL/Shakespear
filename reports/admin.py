from django.contrib import admin

from .models import PageCriteria
from .models import *

# Register your models here.

admin.site.register(Report)
admin.site.register(ReportPage)
admin.site.register(ReportPageMultiGenerated)
admin.site.register(PageCriteria)
admin.site.register(PageLayout)
admin.site.register(ReportPageLink)
