from django.contrib import admin

from apps.merchants.models import Merchant


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "brand_name", "status", "is_active", "created_at"]
    list_filter = ["status", "is_active"]
    search_fields = ["name", "email", "brand_name", "phone_number"]
    autocomplete_fields = ["brand"]
    readonly_fields = ["created_at", "updated_at"]
