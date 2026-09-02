"""Serializers and serializer helpers shared across apps."""

from rest_framework import serializers

from apps.core.models import ContactMessage, NewsletterSubscriber


def absolute_storage_url(request, key):
    """Build a URL for a stored file from its storage key.

    Used for snapshotted references (order line items) where the key is
    recorded at the time of the event and the URL is resolved on the way out.
    That way moving the API to another host, or switching media to S3, fixes
    every historical row at once instead of none of them.
    """
    if not key:
        return None
    if key.startswith(("http://", "https://")):
        # Tolerate rows written before the key-only convention.
        return key

    from django.core.files.storage import default_storage

    try:
        url = default_storage.url(key)
    except (ValueError, NotImplementedError):
        return None
    if url.startswith(("http://", "https://")) or request is None:
        return url
    return request.build_absolute_uri(url)


def absolute_media_url(request, filefield):
    """Return a URL for an uploaded file that resolves from anywhere.

    With local storage `filefield.url` is a root-relative path such as
    /media/products/ab12.jpg. That works when one host serves both the SPA and
    the API, and breaks the moment they are split across two EC2 instances —
    the browser would resolve it against the frontend's host. Making it
    absolute against the incoming request fixes that.

    With S3 the URL is already absolute, so it is returned untouched.
    """
    if not filefield:
        return None
    url = filefield.url
    if url.startswith(("http://", "https://")):
        return url
    if request is not None:
        return request.build_absolute_uri(url)
    return url


class ContactMessageSerializer(serializers.ModelSerializer):
    message = serializers.CharField(min_length=10)

    class Meta:
        model = ContactMessage
        fields = ["id", "name", "email", "message", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_email(self, value):
        # Parity with the MERN app, which rejected a second message from the
        # same address. Implemented as a validation error rather than a unique
        # constraint so the wording stays friendly.
        if ContactMessage.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "We have already received a message from this email address. "
                "We will be in touch shortly."
            )
        return value


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]
        # Uniqueness is handled by get_or_create in the view so that
        # re-subscribing is idempotent instead of a 400.
        extra_kwargs = {"email": {"validators": []}}
