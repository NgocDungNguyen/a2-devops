from django.contrib import admin

from apps.core.models import ActiveVisitor, ContactMessage, NewsletterSubscriber


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "created_at"]
    search_fields = ["name", "email", "message"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["email"]


@admin.register(ActiveVisitor)
class ActiveVisitorAdmin(admin.ModelAdmin):
    """Read-only: rows are written by middleware, not by people."""

    list_display = ["visitor_hash", "last_seen"]
    readonly_fields = ["visitor_hash", "last_seen"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
