from django.contrib import admin
from django.utils.html import format_html

from .models import Prompt, Category, ImagePrompt, Feedback


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


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    # Clean, scannable summary columns
    list_display = ('user', 'subject', 'short_message', 'submitted_at')
    ordering = ('-created_at',)  # most recent first

    # Optional helpers while browsing
    search_fields = ('name', 'email', 'comments')
    list_filter = ('category', 'rating', 'reaction', 'created_at')

    # Read-only: disable add/edit/delete in admin UI
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # --- Column renderers ---
    def user(self, obj):
        who = (obj.name or 'Anonymous').strip()
        if obj.email:
            return f"{who} <{obj.email}>"
        return who
    user.short_description = 'User'

    def subject(self, obj):
        try:
            return obj.get_category_display()
        except Exception:
            return (obj.category or '').title()
    subject.short_description = 'Subject'

    def short_message(self, obj):
        text = (obj.comments or '').strip()
        return (text[:75].rstrip() + '…') if len(text) > 75 else text
    short_message.short_description = 'Message'

    def submitted_at(self, obj):
        return obj.created_at
    submitted_at.admin_order_field = 'created_at'
    submitted_at.short_description = 'Submitted'
