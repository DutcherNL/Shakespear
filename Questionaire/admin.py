from django.contrib import admin
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


class PageAdmin(admin.ModelAdmin):
    class PageQuestionsInlines(admin.TabularInline):
        model = PageEntry
        extra = 1

    class PageReqTechUsefulnessInlines(admin.TabularInline):
        model = PageRequirement
        extra = 0

    inlines = [PageQuestionsInlines, PageReqTechUsefulnessInlines]


admin.site.register(Page, PageAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(AnswerOption, AnswerOptionAdmin)
admin.site.register(PageEntry)
admin.site.register(Inquiry)
admin.site.register(InquiryQuestionAnswer)
admin.site.register(Technology, TechnologyAdmin)
admin.site.register(ScoringDeclaration)
admin.site.register(Score)