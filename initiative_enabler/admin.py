from django.contrib import admin
from django.conf import settings

from .models import *


@admin.register(TechCollective)
class TechCollectiveAdmin(admin.ModelAdmin):
    fields = ('technology', 'description', 'instructions_file', 'instructions_report')
    list_display = ('__str__', 'technology', 'has_restrictions')

    class RestrictionLinkInlines(admin.TabularInline):
        model = TechCollective.restrictions.through
        extra = 0

    def has_restrictions(self, instance):
        return instance.restrictions.count()
    has_restrictions.short_description = 'has restrictions'

    inlines = [RestrictionLinkInlines]


# Register your models here.
admin.site.register(RestrictionRangeAdjustment)
admin.site.register(TechImprovement)
admin.site.register(CollectiveQuestionRestriction)


if settings.SHOW_DEBUG_CLASSES:

    @admin.register(TechCollectiveInterest)
    class TechCollectiveInterestAdmin(admin.ModelAdmin):
        fields = ('inquirer', 'tech_collective', 'is_interested', 'restriction_scopes')

        list_display = ('tech_collective', 'inquirer', 'is_interested', 'last_updated', 'restriction_values')
        list_filter = ('tech_collective',)

        def restriction_values(self, interest):
            res = []
            for value in interest.restriction_scopes.all():
                res.append(value)

            return res

    @admin.register(RestrictionValue)
    class TechCollectiveInterestAdmin(admin.ModelAdmin):
        fields = ('inquirer', 'tech_collective', 'is_interested', 'restriction_scopes')

        list_display = ('__str__', 'restriction', 'value',)
        list_filter = ('restriction',)

    admin.site.register(InitiatedCollective)
    admin.site.register(CollectiveRSVP)
    admin.site.register(CollectiveApprovalResponse)
    admin.site.register(CollectiveDeniedResponse)
