"""Django admin for user accounts.

Subclassing `BaseUserAdmin` rather than plain `ModelAdmin` is the important
line in this file. Django's user admin knows things a generic one does not:
it renders the password as a change-password link instead of a text box, and
it hashes what you type on the add form. Registering User with a plain
ModelAdmin would let a staff member save a *literal* password string into the
hash column, and that account could then never log in.

The fieldsets below exist because this project's User is a custom model —
email instead of a username, plus `role`, `provider` and a link to a merchant
— so the parent class's field lists do not match and have to be restated.

`fieldsets` is the edit form; `add_fieldsets` is the create form, which is
separate because creating a user needs password1/password2 and editing one
must not.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import Address, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # BaseUserAdmin orders by username, which this model does not have.
    ordering = ["-created_at"]
    list_display = ["email", "first_name", "last_name", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    readonly_fields = ["created_at", "updated_at", "last_login"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "phone_number", "avatar")}),
        ("Store", {"fields": ("role", "provider", "merchant")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
            },
        ),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["user", "address", "city", "state", "country", "is_default"]
    list_filter = ["is_default", "country"]
    search_fields = ["user__email", "address", "city"]
    autocomplete_fields = ["user"]
