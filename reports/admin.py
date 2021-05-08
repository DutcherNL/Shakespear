from django.contrib import admin

from .models import *



@admin.register(RenderedReport)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'inquiry', 'created_on')
    list_filter = ('report', 'inquiry')


# Register your models here.

admin.site.register(Report)
admin.site.register(ReportPage)
admin.site.register(ReportPageMultiGenerated)
admin.site.register(PageCriteria)
admin.site.register(PageLayout)
admin.site.register(ReportPageLink)
