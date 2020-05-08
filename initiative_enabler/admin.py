from django.contrib import admin

from .models import *

# Register your models here.

admin.site.register(TechCollective)
admin.site.register(InitiatedCollective)
admin.site.register(CollectiveRSVP)
admin.site.register(CollectiveApprovalResponse)
admin.site.register(CollectiveDeniedResponse)
