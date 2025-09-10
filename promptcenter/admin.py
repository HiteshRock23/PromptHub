from django.contrib import admin

from .models import Prompt


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'role', 'format', 'created_at')
    list_filter = ('category', 'format', 'created_at')
    search_fields = ('title', 'description', 'role', 'content')
