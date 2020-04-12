from django.contrib import admin

from .models import QueuedTask, QueuedCSVDataProcessingTask

# Register your models here.

class QueuedCSVAdmin(admin.ModelAdmin):
    actions = ["process_tasks"]
    list_display = ('id', 'data_table', 'state', 'progress')

    def process_tasks(self, request, queryset):
        for task in queryset.all():
            task.activate()

    process_tasks.short_description = "Process the selected tasks"

admin.site.register(QueuedTask)
admin.site.register(QueuedCSVDataProcessingTask, QueuedCSVAdmin)
