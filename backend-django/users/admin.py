from django.contrib import admin
from .models import Profile, Paper, QuestionBank, PaperQuestion


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("email", "display_name", "role", "firebase_uid", "created_at")
    list_filter = ("role",)
    search_fields = ("email", "display_name", "firebase_uid")
    list_editable = ("role",)


class PaperQuestionInline(admin.TabularInline):
    model = PaperQuestion
    extra = 0
    autocomplete_fields = ["question"]


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ("paper_name", "teacher", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("paper_name", "teacher__email")
    inlines = [PaperQuestionInline]


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ("question_text", "teacher", "marks", "topic", "created_at")
    search_fields = ("question_text", "answer_text", "topic")
    list_filter = ("topic",)