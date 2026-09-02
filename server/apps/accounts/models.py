"""User accounts and delivery addresses.

Start here if you are new to the project: almost every permission decision in
the API is made by reading `User.role`, and this is where that lives.

Swapping in a custom user model takes three pieces, all of them here:

  1. a `User` class, pointed at by AUTH_USER_MODEL in config/settings/base.py
  2. a `UserManager`, because Django calls `User.objects.create_user(...)`
     and `create_superuser(...)` from `manage.py createsuperuser` and from
     the tests, and the default manager expects a username
  3. `USERNAME_FIELD = "email"`, which tells the whole framework — login,
     the admin, password reset — what to identify a person by

It has to be done before the first migration is applied. Changing
AUTH_USER_MODEL on a database that already has tables is genuinely painful,
which is why every Django project either does this on day one or wishes it
had.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models, transaction

from apps.core.models import TimeStampedModel


class Role(models.TextChoices):
    """Application roles.

    Distinct from Django's is_staff / is_superuser, which only govern access
    to /admin/. A user can be a store ADMIN without being a Django superuser
    and vice versa.
    """

    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    MERCHANT = "merchant", "Merchant"


class AuthProvider(models.TextChoices):
    EMAIL = "email", "Email"


class UserManager(BaseUserManager):
    """Email-based user creation.

    `User.objects` is this class, so every `User.objects.filter(...)` in the
    project goes through it. Django itself calls create_user() and
    create_superuser() by name, which is why they exist with those exact
    signatures rather than being ordinary helper functions.
    """

    # Lets a data migration call User.objects.create_user(). Without it,
    # migrations only get a bare manager and would have to set the password
    # hash by hand.
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        # Lower-cased so "Ada@rmit.edu.au" and "ada@rmit.edu.au" cannot become
        # two accounts. The unique constraint on the column is case-sensitive,
        # so it would not catch that on its own.
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            # Merchants invited by an admin have no password until they accept
            # the invitation. An unusable password cannot be used to log in.
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.MEMBER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """A store account.

    Built on AbstractBaseUser rather than AbstractUser because AbstractUser
    ships a required, unique `username` column we would immediately have to
    neuter — the store has always identified people by email.
    """

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=32, blank=True)

    role = models.CharField(
        max_length=16, choices=Role.choices, default=Role.MEMBER, db_index=True
    )
    provider = models.CharField(
        max_length=16, choices=AuthProvider.choices, default=AuthProvider.EMAIL
    )
    avatar = models.URLField(blank=True)

    # Set when an invited seller accepts. SET_NULL rather than CASCADE:
    # deleting a merchant record must not delete the person's account and take
    # their order history with it.
    merchant = models.OneToOneField(
        "merchants.Merchant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False,
        help_text="Can sign in to the Django admin site. Not the same as the store Admin role.",
    )

    # What Django logs people in with, and what `createsuperuser` asks for
    # first. REQUIRED_FIELDS lists the *additional* prompts, and is empty
    # because an email and a password are all an account needs here.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_full_name(self):
        return self.full_name or self.email

    def get_short_name(self):
        return self.first_name or self.email

    # These two are the vocabulary the permission classes in
    # apps/core/permissions.py are written in. Asking "is this user an active
    # merchant?" in one place means the three-part check below cannot be got
    # subtly wrong in the fourth view that needs it.
    @property
    def is_store_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_active_merchant(self):
        """A seller who is allowed to sell *right now*.

        All three parts matter: the role can be MERCHANT while the merchant
        record is missing (an invitation that was never accepted) or
        deactivated (an approval that was withdrawn), and in both cases the
        account must not be able to touch products.
        """
        return (
            self.role == Role.MERCHANT
            and self.merchant is not None
            and self.merchant.is_active
        )


class Address(TimeStampedModel):
    """A saved delivery address."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="addresses", db_index=True
    )
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    country = models.CharField(max_length=120)
    zip_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "-created_at"]
        verbose_name_plural = "addresses"

    def __str__(self):
        return f"{self.address}, {self.city} {self.state}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Exactly one default per user. The MERN app never enforced this, so
        # clicking "make default" twice left two addresses both showing the
        # badge and the checkout picked whichever sorted first.
        super().save(*args, **kwargs)
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
