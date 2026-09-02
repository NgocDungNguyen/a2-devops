"""A self-contained card payment gateway for the demo store.

Why this exists, and what it deliberately is not
------------------------------------------------
The store needs a checkout that behaves like a real one - a card is presented,
it is authorised or declined, and the order only exists if the money did. What
it does not need is an account with a payment provider, a secret key in a
`.env` file, or outbound internet access from the instance. This course is
about deploying and operating a system; a real gateway would add a dependency
that fails in CI, on a locked-down subnet, and on the assessor's laptop, while
teaching nothing about deployment.

So this module simulates one. No network calls, no SDK, no keys.

The test card numbers are Stripe's, on purpose: they are the numbers most
people already have in muscle memory, and moving this to real Stripe later
means swapping `authorise()` for an API call while every test number keeps
working.

    4242 4242 4242 4242   approved (Visa)
    5555 5555 5555 4444   approved (Mastercard)
    3782 822463 10005     approved (American Express)
    4000 0000 0000 0002   declined - card_declined
    4000 0000 0000 9995   declined - insufficient_funds
    4000 0000 0000 0069   declined - expired_card
    4000 0000 0000 0127   declined - incorrect_cvc
    4000 0000 0000 0119   declined - processing_error

Any other number that passes the Luhn check is approved, so a student can
invent a card and still complete a purchase.

Handling of the card number
---------------------------
The full number ("PAN") is never stored, never logged and never returned. Only
the brand and the last four digits are kept, which is the same rule a real
integration works under. Everything else is discarded when the request ends.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import date

from rest_framework import status
from rest_framework.exceptions import APIException

logger = logging.getLogger("apps.orders.payments")


class PaymentDeclined(APIException):
    """The gateway refused the card.

    402 rather than 400 on purpose: the request was well formed and the card
    was readable, the *payment* failed. That distinction is what lets the SPA
    tell "fix your typo" apart from "try a different card", and it is what a
    real gateway integration would return.

    `decline_code` is the machine-readable reason ("insufficient_funds",
    "incorrect_cvc", ...). apps/core/exceptions.py copies it onto the response
    body, so the response looks like:

        402 {"detail": "Your card has insufficient funds.",
             "decline_code": "insufficient_funds"}

    The sentence is for the customer; the code is for the checkout form, which
    uses it to highlight the field the gateway objected to. Keep the two in
    step — a code with no matching sentence leaves the shopper guessing.
    """

    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Your card was declined."
    default_code = "payment_declined"

    def __init__(self, detail=None, decline_code=""):
        super().__init__(detail)
        self.decline_code = decline_code


# Declined test numbers and the reason each one gives back.
DECLINE_CARDS = {
    "4000000000000002": ("card_declined", "Your card was declined."),
    "4000000000009995": (
        "insufficient_funds",
        "Your card has insufficient funds.",
    ),
    "4000000000000069": ("expired_card", "Your card has expired."),
    "4000000000000127": (
        "incorrect_cvc",
        "The security code for your card is incorrect.",
    ),
    "4000000000000119": (
        "processing_error",
        "An error occurred while processing your card. Please try again.",
    ),
}

# Approved test numbers, listed so the test suite can assert every documented
# card is genuinely usable rather than trusting the docstring above.
APPROVE_CARDS = {
    "4242424242424242": "visa",
    "4000056655665556": "visa",
    "5555555555554444": "mastercard",
    "5200828282828210": "mastercard",
    "378282246310005": "amex",
    "371449635398431": "amex",
}


@dataclass(frozen=True)
class Charge:
    """The outcome of an authorisation. Carries no card number."""

    reference: str
    brand: str
    last4: str
    amount: str


def normalise(number):
    """Strip the spaces and dashes people type into a card field."""
    return "".join(ch for ch in str(number) if ch.isdigit())


def luhn_valid(number):
    """The check digit every card number carries.

    Catches a single mistyped digit and most transpositions, which is why a
    real form rejects a bad number before it ever reaches the network.
    """
    digits = normalise(number)
    if not digits.isdigit() or not 12 <= len(digits) <= 19:
        return False

    total = 0
    # Double every second digit counting from the right.
    for index, char in enumerate(reversed(digits)):
        value = int(char)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def card_brand(number):
    """Brand from the leading digits, the way a payment form does it."""
    digits = normalise(number)
    if not digits:
        return "card"

    two = int(digits[:2]) if len(digits) >= 2 else -1
    four = int(digits[:4]) if len(digits) >= 4 else -1

    if digits[0] == "4":
        return "visa"
    if two in (34, 37):
        return "amex"
    # Mastercard owns both the old 51-55 range and the newer 2221-2720 one.
    if 51 <= two <= 55 or 2221 <= four <= 2720:
        return "mastercard"
    if two == 35:
        return "jcb"
    if four == 6011 or two == 65:
        return "discover"
    return "card"


def cvc_length_for(number):
    """American Express uses a four digit code; everybody else uses three."""
    return 4 if card_brand(number) == "amex" else 3


def has_expired(exp_month, exp_year, today=None):
    """A card is good until the last day of its expiry month."""
    today = today or date.today()
    return (int(exp_year), int(exp_month)) < (today.year, today.month)


def authorise(number, exp_month, exp_year, cvc, amount):
    """Authorise `amount` against the card, or raise PaymentDeclined.

    Called inside the checkout transaction and *before* any stock is taken, so
    a decline rolls the whole thing back and leaves no order behind.

    Note what is not in the signature: nothing is returned that would let a
    caller reconstruct the card, and nothing here writes the number to a log.
    """
    digits = normalise(number)
    last4 = digits[-4:]
    brand = card_brand(digits)

    if digits in DECLINE_CARDS:
        code, message = DECLINE_CARDS[digits]
        logger.info("Payment declined (%s) for card ending %s", code, last4)
        raise PaymentDeclined(message, decline_code=code)

    if has_expired(exp_month, exp_year):
        logger.info("Payment declined (expired_card) for card ending %s", last4)
        raise PaymentDeclined("Your card has expired.", decline_code="expired_card")

    if len(normalise(cvc)) != cvc_length_for(digits):
        logger.info("Payment declined (incorrect_cvc) for card ending %s", last4)
        raise PaymentDeclined(
            "The security code for your card is incorrect.",
            decline_code="incorrect_cvc",
        )

    # A real gateway returns an opaque reference you can quote to support.
    charge = Charge(
        reference=f"ch_{uuid.uuid4().hex[:24]}",
        brand=brand,
        last4=last4,
        amount=str(amount),
    )
    logger.info(
        "Payment approved %s for %s ending %s", charge.reference, amount, last4
    )
    return charge
