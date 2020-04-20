from django.contrib import admin

from .models import *

# Register your models here.

admin.site.register(MailTask)
admin.site.register(TimedMailTask)
admin.site.register(TriggeredMailTask)
