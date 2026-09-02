"""Django admin for the catalogue.

The admin at /admin/ is scaffolding that Django generates from the models —
you get a working back office for free, and these classes only say how it
should look. It is a staff tool, not the API: it talks to the models
directly, so the rules enforced by the serializers and services do not apply
here. Administrators get the same catalogue management through the SPA's
dashboard, which does go through the API.

Three settings do most of the work in each class below:
    list_display     the columns in the table
    list_filter      the filter sidebar
    search_fields    what the search box looks in

`search_fields` also has a side effect worth knowing: a model can only be used
in another model's `autocomplete_fields` if its own admin declares
search_fields. That is why Brand has it even though nobody searches brands —
ProductAdmin's brand autocomplete needs it.
"""

from django.contrib import admin

from apps.catalog.models import Brand, Category, Product


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug", "created_at", "updated_at"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug", "created_at", "updated_at"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "price", "quantity", "brand", "is_active"]
    list_filter = ["is_active", "taxable", "brand"]
    search_fields = ["name", "sku", "slug"]
    # A plain dropdown would load every brand into the page. Autocomplete
    # fetches matches as you type instead, which matters once a real
    # deployment has more than a demo catalogue in it.
    autocomplete_fields = ["brand"]
    filter_horizontal = ["categories"]
    # Slugs are derived from the name by SluggedModel.save(), and they appear
    # in URLs that may already be bookmarked or indexed. Editing one by hand
    # here would break those links with no warning and no redirect.
    readonly_fields = ["slug", "created_at", "updated_at"]
