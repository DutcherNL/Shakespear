from django.contrib import admin, messages
from django.conf import settings
from django.db.models import ProtectedError

from .models import *

# Register your models here.


class QuestionAdmin(admin.ModelAdmin):

    class QuestionAnwerOptionsInlines(admin.TabularInline):
        model = AnswerOption
        extra = 0

    inlines = [QuestionAnwerOptionsInlines]


class AnswerScoringFilter(admin.SimpleListFilter):
    """
    A filter that filters users on the time they've had a negative balance.
    """
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Adjusted Scoring values'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'adj_scoring_note'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples representing all the declarations
        as displayed in the table
        """

        list_of_declarations = []
        queryset = ScoringDeclaration.objects.order_by('name')
        for declaration in queryset:
            list_of_declarations.append(
                (str(declaration.id), declaration.name)
            )
        return sorted(list_of_declarations, key=lambda tp: tp[1])

    def queryset(self, request, queryset):
        """
        Returns the filtered querysets containing all members of the selected associations
        """

        # If no selection is made, return the entire query
        if self.value():
            return queryset.filter(answerscoring__declaration=self.value())
        return queryset


class AnswerOptionAdmin(admin.ModelAdmin):
    class AnswerScoringInlines(admin.TabularInline):
        model = AnswerScoring
        extra = 0

    inlines = [AnswerScoringInlines]

    list_display = ('__str__', 'question', 'answer',)
    list_filter = ('question', AnswerScoringFilter)


class TechnologyAdmin(admin.ModelAdmin):
    class TechScoreLinkInlines(admin.TabularInline):
        model = TechScoreLink
        extra = 1

    inlines = [TechScoreLinkInlines]

    actions = ['resolve_group_conflicts', 'convert_to_techgroup']

    def resolve_group_conflicts(self, request, queryset):
        merge_succesful = 0

        for obj in queryset:
            techs = Technology.objects.filter(name=obj.name)
            if techs.count() > 1:
                # There is a conflict
                non_group = techs.get(techgroup__isnull=True)
                tech_group = TechGroup.objects.get(technology_ptr__name=obj.name)
                old_group = tech_group.technology_ptr
                tech_group.technology_ptr = non_group
                tech_group.save()
                tech_group.sub_technologies.filter(name=obj.name).delete()
                tech_group.sub_technologies.remove(non_group)
                try:
                    old_group.delete()
                    merge_succesful = merge_succesful + 1
                except ProtectedError:
                    messages.error(request, "Could not delete {object}, object is protected".format(object=old_group))

        messages.success(request, "Succesfully merged {successes} tech groups".format(merge_succesful))

    def convert_to_techgroup(self, request, queryset):
        merge_succesful = 0

        for obj in queryset:
            if obj.techgroups.count() == 0:
                techgroup = TechGroup(technology_ptr=obj)
                techgroup.name = obj.name
                techgroup.short_text = obj.short_text
                techgroup.icon = obj.icon
                techgroup.information_page = obj.information_page

                techgroup.save()
                merge_succesful = merge_succesful + 1

        messages.info(request, "Successfully converted {number} technologies to technologygroups".
                      format(number=merge_succesful))


class AnswerScoringAdmin(admin.ModelAdmin):
    class AnswerScoreNoteInlines(admin.TabularInline):
        model = AnswerScoringNote
        extra = 0
        filter_horizontal = ('exclude_on', 'include_on',)

    inlines = [AnswerScoreNoteInlines]


class PageAdmin(admin.ModelAdmin):
    class PageQuestionsInlines(admin.TabularInline):
        model = PageEntryQuestion
        exclude = ("entry_type",)
        extra = 0

    class PageTextsInlines(admin.TabularInline):
        model = PageEntryText
        exclude = ("entry_type",)
        extra = 0

    class PageReqTechUsefulnessInlines(admin.TabularInline):
        model = PageRequirement
        extra = 0

    inlines = [PageTextsInlines, PageQuestionsInlines, PageReqTechUsefulnessInlines]


class AnswerNoteAdmin(admin.ModelAdmin):
    filter_horizontal = ('exclude_on', 'include_on',)

    list_display = ('__str__', 'scoring', 'technology',)
    list_filter = ('technology',)


admin.site.register(Page, PageAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(AnswerOption, AnswerOptionAdmin)
admin.site.register(ScoringDeclaration)
admin.site.register(Technology, TechnologyAdmin)
admin.site.register(TechGroup, TechnologyAdmin)
admin.site.register(AnswerScoring, AnswerScoringAdmin)
admin.site.register(AnswerScoringNote, AnswerNoteAdmin)
admin.site.register(ExternalQuestionSource)

if settings.SHOW_DEBUG_CLASSES:
    admin.site.register(Inquirer)
    admin.site.register(Score)
    admin.site.register(Inquiry)
    admin.site.register(InquiryQuestionAnswer)
    admin.site.register(TechScoreLink)

