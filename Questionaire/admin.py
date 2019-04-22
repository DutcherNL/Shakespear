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


admin.site.register(Page)
admin.site.register(Question, QuestionAdmin)
admin.site.register(AnswerOption, AnswerOptionAdmin)
admin.site.register(PageEntry)
admin.site.register(Inquiry)
admin.site.register(InquiryQuestionAnswer)
admin.site.register(Technology)
admin.site.register(TechnologyScore)