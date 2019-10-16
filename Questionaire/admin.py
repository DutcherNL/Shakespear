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


class AnswerOptionAdmin(admin.ModelAdmin):
    class AnswerScoringInlines(admin.TabularInline):
        model = AnswerScoring
        extra = 0

    inlines = [AnswerScoringInlines]


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
        filter_horizontal = ('exclude_on','include_on',)

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

