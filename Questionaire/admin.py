from django.contrib import admin, messages
from django.conf import settings
from django.db.models import ProtectedError

from .models import *
from tools.csv_translations import ExportCsvMixin

# Register your models here.


class QuestionAdmin(ExportCsvMixin, admin.ModelAdmin):
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


class AnswerOptionAdmin(ExportCsvMixin, admin.ModelAdmin):
    exclude_csv_fields = ['image']

    class AnswerScoringInlines(admin.TabularInline):
        model = AnswerScoring
        extra = 0

    inlines = [AnswerScoringInlines]

    list_display = ('__str__', 'question', 'answer',)
    list_filter = ('question', AnswerScoringFilter)


class TechnologyAdmin(ExportCsvMixin, admin.ModelAdmin):
    exclude_csv_fields = ['icon', 'information_page']

    class TechScoreLinkInlines(admin.TabularInline):
        model = TechScoreLink
        extra = 1

    inlines = [TechScoreLinkInlines]

    actions = ['resolve_group_conflicts', 'convert_to_techgroup']

    def resolve_group_conflicts(self, request, queryset):
        """ A method that attempts to resolve conflicts when a tech group and a technology are not related, but share
        the same name

        :param request:
        :param queryset:
        """
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
        """ Converts a technology to a tech group """
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


class AnswerScoringAdmin(ExportCsvMixin, admin.ModelAdmin):
    exclude_csv_fields = ['answer_option']
    add_csv_fields = ['answer_option__question__name', 'answer_option__answer']

    class AnswerScoreNoteInlines(admin.TabularInline):
        model = AnswerScoringNote
        extra = 0
        filter_horizontal = ('exclude_on', 'include_on',)

    inlines = [AnswerScoreNoteInlines]


class AnswerNoteAdmin(ExportCsvMixin, admin.ModelAdmin):
    exclude_csv_fields = ['scoring']
    add_csv_fields = ['scoring__answer_option__question__name',
                      'scoring__answer_option__answer',
                      'scoring__declaration__name']

    filter_horizontal = ('exclude_on', 'include_on',)

    list_display = ('__str__', 'scoring', 'technology',)
    list_filter = ('technology',)


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


class ScoreDeclarationMixin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ('name', 'display_name', 'score_start_value',)


class TechScoreLinkAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ('score_declaration', 'technology', 'score_threshold_approve', 'score_threshold_deny')


class InquirerAdmin(admin.ModelAdmin):
    list_display = ('get_email', 'created_on',)
    list_filter = ('created_on',)


class InquiryAdmin(admin.ModelAdmin):
    list_display = ('get_owner', 'current_page', 'is_complete', 'last_visited')
    list_filter = ('is_complete', 'created_on')


admin.site.register(Page, PageAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(AnswerOption, AnswerOptionAdmin)
admin.site.register(ScoringDeclaration, ScoreDeclarationMixin)
admin.site.register(Technology, TechnologyAdmin)
admin.site.register(TechGroup, TechnologyAdmin)
admin.site.register(AnswerScoring, AnswerScoringAdmin)
admin.site.register(AnswerScoringNote, AnswerNoteAdmin)
admin.site.register(ExternalQuestionSource)
admin.site.register(TechScoreLink, TechScoreLinkAdmin)

admin.site.register(Inquiry, InquiryAdmin)
admin.site.register(Inquirer, InquirerAdmin)


if settings.SHOW_DEBUG_CLASSES:
    admin.site.register(Score)
    admin.site.register(InquiryQuestionAnswer)

