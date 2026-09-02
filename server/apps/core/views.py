"""Health probes, public runtime config, and the contact/newsletter endpoints."""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connections
from django.db.utils import OperationalError
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.emails import send_templated_mail
from apps.core.models import ActiveVisitor, ContactMessage, NewsletterSubscriber
from apps.core.serializers import (
    ContactMessageSerializer,
    NewsletterSubscriberSerializer,
)

logger = logging.getLogger("apps.core.health")


class HealthzView(APIView):
    """Liveness probe.

    Answers one question: is this process able to serve a request at all?
    It deliberately touches nothing — no database, no storage, no cache. A
    liveness probe that checks its dependencies will restart a perfectly
    healthy application server because the database is briefly slow, which
    turns a small outage into a restart loop.

    Use this for the ELB/ALB target group health check and the Kubernetes
    livenessProbe.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(tags=["infrastructure"], responses={200: dict})
    def get(self, request):
        return Response({"status": "ok"})


class ReadyzView(APIView):
    """Readiness probe.

    Answers a different question: is this process able to serve *useful*
    traffic right now? It checks the dependencies a request actually needs.
    Failing readiness takes the instance out of the load balancer rotation
    without killing it, so it can recover and rejoin.

    Use this for the Kubernetes readinessProbe, for a Compose
    `depends_on: condition: service_healthy`, and as the smoke test an Ansible
    deploy polls before moving on to the next host.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(tags=["infrastructure"], responses={200: dict, 503: dict})
    def get(self, request):
        checks = {}
        healthy = True

        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks["database"] = "ok"
        except OperationalError as exc:
            logger.error("Readiness check failed: database unreachable: %s", exc)
            checks["database"] = "unavailable"
            healthy = False

        try:
            default_storage.exists("__readyz_probe__")
            checks["storage"] = "ok"
        except Exception as exc:  # noqa: BLE001 - any storage error means not ready
            logger.error("Readiness check failed: storage unreachable: %s", exc)
            checks["storage"] = "unavailable"
            healthy = False

        return Response(
            checks,
            status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class VersionView(APIView):
    """What is actually running on this box.

    Three lines of code that save an argument during a blue/green cutover:
    curl the endpoint through the load balancer and you know which build is
    serving traffic.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(tags=["infrastructure"], responses={200: dict})
    def get(self, request):
        return Response(
            {"version": settings.APP_VERSION, "commit": settings.GIT_COMMIT}
        )


class ActivityMetricsView(APIView):
    """How many distinct visitors the store has seen recently.

    Read by the CloudWatch metrics publisher (monitoring/publish-app-metrics.sh)
    once a minute, and pleasant to eyeball by hand during a demo. Lives
    outside /api/'s auth stack for the same reason the probes do: a metrics
    scraper should not need a JWT.

    The numbers come from the ActiveVisitor table, which every backend
    replica writes to via VisitorActivityMiddleware — so this answers for the
    whole fleet, not just the replica that happened to serve this request.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(tags=["infrastructure"], responses={200: dict})
    def get(self, request):
        now = timezone.now()
        visitors = ActiveVisitor.objects
        payload = {
            "active_visitors_1m": visitors.filter(
                last_seen__gte=now - timedelta(minutes=1)
            ).count(),
            "active_visitors_5m": visitors.filter(
                last_seen__gte=now - timedelta(minutes=5)
            ).count(),
            "active_visitors_15m": visitors.filter(
                last_seen__gte=now - timedelta(minutes=15)
            ).count(),
        }
        # Opportunistic pruning: a day-old row can never influence any
        # window again, and doing it here saves a cron job.
        visitors.filter(last_seen__lt=now - timedelta(hours=24)).delete()
        return Response(payload)


class PublicConfigView(APIView):
    """Store rules the SPA needs but should not hard-code.

    The tax rate lives in one place — server settings — so changing it does
    not require rebuilding the frontend bundle.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(tags=["infrastructure"], responses={200: dict})
    def get(self, request):
        return Response(
            {
                "sales_tax_rate": settings.SALES_TAX_RATE,
                "sales_tax_state_code": settings.SALES_TAX_STATE_CODE,
                "sales_tax_state_name": settings.SALES_TAX_STATE_NAME,
                "currency": settings.STORE_CURRENCY,
                "currency_symbol": settings.STORE_CURRENCY_SYMBOL,
            }
        )


class ContactCreateView(CreateAPIView):
    """POST /api/contact/ — the public "Get in touch" form."""

    serializer_class = ContactMessageSerializer
    queryset = ContactMessage.objects.all()
    permission_classes = [AllowAny]
    throttle_scope = "contact"

    def perform_create(self, serializer):
        contact = serializer.save()
        send_templated_mail(
            to=[settings.STORE_NOTIFICATION_EMAIL],
            template_name="contact",
            subject="New contact form submission",
            context={"contact": contact},
        )


class NewsletterSubscribeView(CreateAPIView):
    """POST /api/newsletter/subscribe/ — footer signup form."""

    serializer_class = NewsletterSubscriberSerializer
    queryset = NewsletterSubscriber.objects.all()
    permission_classes = [AllowAny]
    throttle_scope = "newsletter"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # Re-subscribing someone who previously unsubscribed should just work
        # rather than colliding with the unique constraint.
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email, defaults={"is_active": True}
        )
        if not created and not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=["is_active", "updated_at"])

        send_templated_mail(
            to=[email],
            template_name="newsletter_subscription",
            subject="You are subscribed to the RMIT Store newsletter",
            context={"email": email},
        )
        return Response(
            {"detail": "You have been subscribed to our newsletter."},
            status=status.HTTP_201_CREATED,
        )
