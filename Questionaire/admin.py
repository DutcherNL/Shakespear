from django.contrib import admin
from .models import *

# Register your models here.


class QuestionAnwerOptionsInlines(admin.TabularInline):
    model = AnswerOption
    extra = 0


class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionAnwerOptionsInlines]


class AnswerScoringInlines(admin.TabularInline):
    model = AnswerScoring
    extra = 0


class AnswerOptionAdmin(admin.ModelAdmin):
    inlines = [AnswerScoringInlines]


class PageAdmin(admin.ModelAdmin):
    class PageQuestionsInlines(admin.TabularInline):
        model = PageEntry
        extra = 1

    class PageReqTechUsefulnessInlines(admin.TabularInline):
        model = PageRequirementTechUsefulness
        extra = 0

    inlines = [PageQuestionsInlines, PageReqTechUsefulnessInlines]


admin.site.register(Page, PageAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(AnswerOption, AnswerOptionAdmin)
admin.site.register(PageEntry)
admin.site.register(Inquiry)
admin.site.register(InquiryQuestionAnswer)
admin.site.register(Technology)
admin.site.register(TechnologyScore)
admin.site.register(PageRequirementTechUsefulness)