from django.contrib import admin
from django.utils.html import format_html

from .models import Prompt, Category, ImagePrompt


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'role', 'format', 'created_at')
    list_filter = ('category', 'format', 'created_at')
    search_fields = ('title', 'description', 'role', 'content', 'prompt')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'created_at')


@admin.register(ImagePrompt)
class ImagePromptAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'title', 'created_at')
    search_fields = ('title', 'prompt_text')
    readonly_fields = ('preview',)

    def thumb(self, obj):  # pragma: no cover
        if obj.image and hasattr(obj.image, 'url'):
            return format_html('<img src="{}" style="height:42px;width:auto;border-radius:6px;" />', obj.image.url)
        return '-'
    thumb.short_description = 'Preview'

    def preview(self, obj):  # pragma: no cover
        if obj.image and hasattr(obj.image, 'url'):
            return format_html('<img src="{}" style="max-width:100%;height:auto;border-radius:8px;" />', obj.image.url)
        return '-'
