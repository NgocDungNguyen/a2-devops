"""Abstract bases and the two small standalone models (contact, newsletter)."""

from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    """Adds created_at / updated_at to every model in the project.

    The MERN app hand-rolled `created` and `updated` date fields on each
    schema and only sometimes set them. auto_now_add / auto_now make it
    automatic and consistent.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SluggedModel(TimeStampedModel):
    """URL slug generated from a source field, with collision handling.

    Replaces the `mongoose-slug-generator` plugin used on Brand, Category and
    Product. One deliberate difference: the slug is only generated when blank,
    so renaming a product does not break links that already point at it.
    Clear the slug to force regeneration.
    """

    slug_source_field = "name"
    slug_max_length = 120

    slug = models.SlugField(max_length=140, unique=True, blank=True, db_index=True)

    class Meta:
        abstract = True

    def _generate_unique_slug(self):
        source = getattr(self, self.slug_source_field) or ""
        base = slugify(source)[: self.slug_max_length] or "item"
        candidate = base
        suffix = 2
        model = self.__class__
        while (
            model.objects.filter(slug=candidate).exclude(pk=self.pk).exists()
        ):
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)


class ContactMessage(TimeStampedModel):
    """A submission from the public /contact form."""

    name = models.CharField(max_length=120)
    email = models.EmailField(db_index=True)
    message = models.TextField()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "contact message"

    def __str__(self):
        return f"{self.name} <{self.email}>"


class ActiveVisitor(models.Model):
    """One row per distinct visitor recently seen by any backend replica.

    Written by ``VisitorActivityMiddleware`` and read by /metrics/activity/,
    which feeds the "how many people are on the store right now" number on
    the CloudWatch dashboard.

    Stored in the shared database rather than a per-process cache on purpose:
    with several backend replicas behind a load balancer, each process only
    sees a slice of the traffic — the database is the one place they all
    agree on. The hash is sha256(client IP + user agent), so no personal data
    is stored and anonymous shoppers count too, which is what "people
    accessing the store" actually means for a shop.
    """

    visitor_hash = models.CharField(max_length=64, unique=True)
    last_seen = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = "active visitor"

    def __str__(self):
        return f"{self.visitor_hash[:12]} @ {self.last_seen:%Y-%m-%d %H:%M:%S}"


class NewsletterSubscriber(TimeStampedModel):
    """A newsletter signup.

    The MERN app forwarded these to Mailchimp, which was never configured — so
    the endpoint always failed. A local table makes the feature work and gives
    the admin something to look at.
    """

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email
