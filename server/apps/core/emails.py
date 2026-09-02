"""
Outbound email.

One façade, `send_templated_mail`, renders templates/email/<name>.txt (and
.html when present) and sends through whatever EMAIL_BACKEND is configured.

Failures are logged, never raised. A checkout must not 500 because SES is
briefly unreachable — the order is already committed by the time the receipt
is sent, and losing the receipt is far better than losing the order.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_templated_mail(to, template_name, subject, context=None):
    """Render and send one notification.

    Args:
        to: list of recipient addresses.
        template_name: base name under templates/email/, without extension.
        subject: subject line.
        context: template context.

    Returns True if the message was handed to the backend, False otherwise.
    """
    context = dict(context or {})
    context.setdefault("client_url", settings.CLIENT_URL)
    context.setdefault("store_name", "RMIT Store")

    try:
        body = render_to_string(f"email/{template_name}.txt", context)
    except TemplateDoesNotExist:
        logger.error("Email template email/%s.txt does not exist", template_name)
        return False

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=list(to),
        )
        try:
            html = render_to_string(f"email/{template_name}.html", context)
        except TemplateDoesNotExist:
            html = None
        if html:
            message.attach_alternative(html, "text/html")

        message.send(fail_silently=False)
        logger.info("Sent '%s' email to %s", template_name, ", ".join(to))
        return True
    except Exception:  # noqa: BLE001 - email must never break a request
        logger.exception("Failed to send '%s' email to %s", template_name, to)
        return False
