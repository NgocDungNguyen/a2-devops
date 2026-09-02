"""Custom DRF exception handler."""

import logging

from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def _first_message(data):
    """Pull one human-readable sentence out of a DRF error body.

    DRF error bodies are trees: {"email": ["..."]} for a flat form, and
    {"payment": {"number": ["..."]}} once a serializer is nested inside
    another (checkout posts the card under `payment`). This walks down to the
    first actual sentence and labels it with the field it belongs to.

    Only the field name closest to the message is used as the label. Prefixing
    at every level would produce "payment: number: That card number is not
    valid", and a toast reading like a stack trace helps nobody.
    """
    if isinstance(data, str):
        return data
    if isinstance(data, list) and data:
        return _first_message(data[0])
    if isinstance(data, dict):
        if "detail" in data:
            return _first_message(data["detail"])
        for key, value in data.items():
            message = _first_message(value)
            if not message:
                continue
            # A nested serializer has already labelled the message with the
            # field that actually failed, so leave it alone.
            if isinstance(value, dict):
                return message
            # "email: A user with this email already exists."
            return message if key == "non_field_errors" else f"{key}: {message}"
    return ""


def api_exception_handler(exc, context):
    """Guarantee every error body carries a `detail` string.

    Field-level errors are still returned in full so a form can highlight the
    offending input; `detail` is added alongside so the toast layer in the SPA
    has exactly one place to read a message from, whatever the error shape.
    """
    if isinstance(exc, ProtectedError):
        # Raised when deleting a Product that appears on a historical order.
        return Response(
            {
                "detail": (
                    "This record is referenced by existing orders and cannot be "
                    "deleted. Deactivate it instead so order history stays intact."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )

    response = drf_exception_handler(exc, context)

    if response is None:
        # Not a DRF exception — let Django's 500 handling deal with it, but
        # make sure it is in the log with a traceback.
        logger.exception("Unhandled exception in %s", context.get("view"))
        return None

    if isinstance(response.data, dict):
        # `detail` must always be a plain string. Raising
        # ValidationError({"detail": "..."}) leaves it wrapped in a list, which
        # would make the SPA render ["Something went wrong"] in a toast.
        if "detail" in response.data:
            flattened = _first_message(response.data["detail"])
            if flattened:
                response.data["detail"] = flattened
        else:
            message = _first_message(response.data)
            if message:
                response.data["detail"] = message
    elif isinstance(response.data, list):
        response.data = {"detail": _first_message(response.data) or "Invalid input.",
                         "errors": response.data}

    # Machine-readable extras that some exceptions carry alongside the
    # sentence. PaymentDeclined sets `decline_code` ("insufficient_funds",
    # "incorrect_cvc", ...) so the checkout form can point at the field the
    # gateway objected to instead of only showing a toast. Read with getattr
    # rather than importing the exception: core is the bottom of the app
    # stack and must not depend on the apps built on top of it.
    decline_code = getattr(exc, "decline_code", "")
    if decline_code and isinstance(response.data, dict):
        response.data["decline_code"] = decline_code

    return response
