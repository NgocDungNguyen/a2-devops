from django.contrib import admin

from apps.reviews.models import Review, Wishlist


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["title", "product", "user", "rating", "status", "created_at"]
    list_filter = ["status", "rating", "is_recommended"]
    search_fields = ["title", "review", "user__email", "product__name"]
    autocomplete_fields = ["product", "user"]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "is_liked", "updated_at"]
    list_filter = ["is_liked"]
    search_fields = ["user__email", "product__name"]
    autocomplete_fields = ["product", "user"]
