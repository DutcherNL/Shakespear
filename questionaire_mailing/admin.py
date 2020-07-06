from django.contrib import admin

from .models import *
from Questionaire.models import Inquiry

# Register your models here.


@admin.register(TimedMailTask)
class TimedMailTaskAdmin(admin.ModelAdmin):
    fields = ('name', 'description', 'active', 'trigger', 'days_after')
    list_display = ('name', 'active', 'trigger', 'days_after')
    actions = ['mark_as_send']

    def mark_as_send(modeladmin, request, queryset):
        for mail_task in queryset:
            for inquiry in Inquiry.objects.all():
                if not ProcessedMail.objects.filter(mail=mail_task, inquiry=inquiry).exists():
                    ProcessedMail.objects.create(
                        mail=mail_task,
                        inquiry=inquiry,
                        was_applicable=False
                    )
    mark_as_send.short_description = "Mark mail task as processed for all current inquiries"


admin.site.register(MailTask)
admin.site.register(TriggeredMailTask)
admin.site.register(ProcessedMail)
