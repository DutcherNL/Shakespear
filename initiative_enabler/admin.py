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
        fields = ('inquirer', 'tech_collective', 'is_interested')

        list_display = ('__str__', 'inquirer', 'is_interested')
        list_filter = ('inquirer',)

        class RestrictionsInlines(admin.TabularInline):
            model = TechCollectiveInterest.restriction_scopes.through
            fields = ('restriction', 'value')
            readonly_fields = ('restriction', 'value')
            extra = 0

            def has_add_permission(self, request, obj):
                # This should only display info, not allow changing
                return False

            def restriction(self, instance):
                return instance.restrictionvalue.restriction.name
            restriction.short_description = 'restriction name'

            def value(self, instance):
                return instance.restrictionvalue.value
            value.short_description = 'local value'

        inlines = [RestrictionsInlines]

    admin.site.register(RestrictionValue)
    admin.site.register(InitiatedCollective)
    admin.site.register(CollectiveRSVP)
    admin.site.register(CollectiveApprovalResponse)
    admin.site.register(CollectiveDeniedResponse)
