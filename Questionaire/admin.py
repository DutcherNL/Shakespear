from django.contrib import admin
from .model_files.base_models import *
from .model_files.tech_scoring_models import *

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
admin.site.register(Inquirer)
admin.site.register(Technology, TechnologyAdmin)
admin.site.register(AnswerScoring, AnswerScoringAdmin)
admin.site.register(Score)
admin.site.register(Inquiry)
admin.site.register(InquiryQuestionAnswer)
admin.site.register(AnswerScoringNote, AnswerNoteAdmin)
admin.site.register(ExternalQuestionSource)
