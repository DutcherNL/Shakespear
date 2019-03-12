from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Page)
admin.site.register(Question)
admin.site.register(PageEntry)
admin.site.register(Inquiry)
admin.site.register(InquiryQuestionAnswer)