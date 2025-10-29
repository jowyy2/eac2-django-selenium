from django.contrib import admin
from .models import Question, Choice
# Register your models here.

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2  # 2 respuestas por defecto

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "question_text", "pub_date")
    inlines = [ChoiceInline]

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "choice_text", "votes")
