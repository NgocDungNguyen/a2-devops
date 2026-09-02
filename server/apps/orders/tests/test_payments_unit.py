"""
Unit tests — the simulated payment gateway (apps/orders/payments.py).

Why these are "unit" tests rather than "integration": every function under
test here is a pure function of its arguments. None of them touch the
database, the network, or Django's request/response cycle — `authorise()`
raises a plain Python exception, it does not render an HTTP response. That
means these tests need no database and no APIClient, and they run in
milliseconds. TestCase (not TransactionTestCase / APITestCase) is used only
for its assertion helpers and to fit the same `manage.py test` discovery as
every other suite; no `@override_settings`, fixtures or `--keepdb` behaviour
depends on it.

What this file is protecting: the eight documented test-card outcomes in the
README's "Paying for an order" table, and the four checks — Luhn, brand,
expiry, CVC length — that `authorise()` performs before it will approve a
charge. A regression here (an off-by-one in the Luhn algorithm, a decline
code returning the wrong HTTP semantics, a card silently misclassified as a
different brand) would corrupt every order placed against it, so it is worth
pinning down independently of the checkout flow that calls it.
"""

from datetime import date

import pytest
from django.test import SimpleTestCase

from apps.orders.payments import (
    APPROVE_CARDS,
    DECLINE_CARDS,
    Charge,
    PaymentDeclined,
    authorise,
    card_brand,
    cvc_length_for,
    has_expired,
    luhn_valid,
    normalise,
)

pytestmark = pytest.mark.unit

FUTURE_EXP = {"exp_month": 12, "exp_year": date.today().year + 3}


class NormaliseTests(SimpleTestCase):
    """Strips whatever punctuation a human types into a card field."""

    def test_strips_spaces_and_dashes(self):
        self.assertEqual(normalise("4242 4242 4242 4242"), "4242424242424242")
        self.assertEqual(normalise("4242-4242-4242-4242"), "4242424242424242")

    def test_leaves_bare_digits_alone(self):
        self.assertEqual(normalise("4242424242424242"), "4242424242424242")

    def test_drops_non_digit_characters_entirely(self):
        self.assertEqual(normalise("42a42 42#42 4242 4242"), "4242424242424242")


class LuhnValidTests(SimpleTestCase):
    """The check digit every real card number carries."""

    def test_accepts_every_documented_approved_card(self):
        for number in APPROVE_CARDS:
            with self.subTest(number=number):
                self.assertTrue(luhn_valid(number))

    def test_accepts_every_documented_declined_card(self):
        # Declines happen for business reasons (insufficient funds, an
        # expired card), not because the number itself is malformed — a
        # decline card must still pass the check digit.
        for number in DECLINE_CARDS:
            with self.subTest(number=number):
                self.assertTrue(luhn_valid(number))

    def test_rejects_a_single_mistyped_digit(self):
        # The last digit of 4242 4242 4242 4242, flipped.
        self.assertFalse(luhn_valid("4242424242424241"))

    def test_rejects_too_short_a_number(self):
        self.assertFalse(luhn_valid("4242"))

    def test_rejects_non_numeric_input(self):
        self.assertFalse(luhn_valid("not-a-card-number"))

    def test_rejects_empty_string(self):
        self.assertFalse(luhn_valid(""))


class CardBrandTests(SimpleTestCase):
    def test_visa_starts_with_4(self):
        self.assertEqual(card_brand("4242424242424242"), "visa")

    def test_mastercard_51_to_55_range(self):
        self.assertEqual(card_brand("5555555555554444"), "mastercard")

    def test_mastercard_2221_to_2720_range(self):
        self.assertEqual(card_brand("2221000000000009"), "mastercard")

    def test_amex_34_or_37(self):
        self.assertEqual(card_brand("378282246310005"), "amex")
        self.assertEqual(card_brand("341111111111111"), "amex")

    def test_discover(self):
        self.assertEqual(card_brand("6011111111111117"), "discover")

    def test_jcb(self):
        self.assertEqual(card_brand("3530111333300000"), "jcb")

    def test_unrecognised_prefix_falls_back_to_generic_card(self):
        self.assertEqual(card_brand("9999999999999999"), "card")

    def test_empty_input_falls_back_to_generic_card(self):
        self.assertEqual(card_brand(""), "card")

    def test_every_documented_approve_card_matches_its_labelled_brand(self):
        for number, expected_brand in APPROVE_CARDS.items():
            with self.subTest(number=number):
                self.assertEqual(card_brand(number), expected_brand)


class CvcLengthTests(SimpleTestCase):
    def test_amex_needs_four_digits(self):
        self.assertEqual(cvc_length_for("378282246310005"), 4)

    def test_everyone_else_needs_three(self):
        self.assertEqual(cvc_length_for("4242424242424242"), 3)
        self.assertEqual(cvc_length_for("5555555555554444"), 3)


class HasExpiredTests(SimpleTestCase):
    """A card is good through the last day of its expiry month."""

    def test_future_year_is_not_expired(self):
        today = date(2026, 6, 15)
        self.assertFalse(has_expired(1, 2027, today=today))

    def test_current_month_is_not_expired(self):
        today = date(2026, 6, 15)
        self.assertFalse(has_expired(6, 2026, today=today))

    def test_next_month_this_year_is_not_expired(self):
        today = date(2026, 6, 15)
        self.assertFalse(has_expired(7, 2026, today=today))

    def test_last_month_this_year_is_expired(self):
        today = date(2026, 6, 15)
        self.assertTrue(has_expired(5, 2026, today=today))

    def test_past_year_is_expired_regardless_of_month(self):
        today = date(2026, 6, 15)
        self.assertTrue(has_expired(12, 2025, today=today))


class AuthoriseApprovedCardsTests(SimpleTestCase):
    """Every card the README's table promises will succeed, actually does."""

    def test_every_documented_approve_card_is_charged(self):
        for number, expected_brand in APPROVE_CARDS.items():
            with self.subTest(number=number):
                charge = authorise(
                    number=number,
                    cvc="1234" if expected_brand == "amex" else "123",
                    amount="75.15",
                    **FUTURE_EXP,
                )
                self.assertIsInstance(charge, Charge)
                self.assertEqual(charge.brand, expected_brand)
                self.assertEqual(charge.last4, number[-4:])
                self.assertEqual(charge.amount, "75.15")

    def test_charge_reference_is_unique_per_authorisation(self):
        first = authorise(number="4242424242424242", cvc="123", amount="10.00", **FUTURE_EXP)
        second = authorise(number="4242424242424242", cvc="123", amount="10.00", **FUTURE_EXP)
        self.assertNotEqual(first.reference, second.reference)
        self.assertTrue(first.reference.startswith("ch_"))

    def test_charge_never_carries_the_card_number(self):
        charge = authorise(number="4242424242424242", cvc="123", amount="10.00", **FUTURE_EXP)
        for value in vars(charge).values():
            self.assertNotIn("4242424242424242", str(value))

    def test_spaces_and_dashes_in_the_number_are_tolerated(self):
        charge = authorise(
            number="4242 4242 4242 4242", cvc="123", amount="10.00", **FUTURE_EXP
        )
        self.assertEqual(charge.brand, "visa")

    def test_a_novel_luhn_valid_card_not_on_either_list_is_approved(self):
        # payments.py's docstring promises this explicitly: "Any other number
        # that passes the Luhn check is approved, so a student can invent a
        # card and still complete a purchase." 4111 1111 1111 1111 is the
        # generic Luhn-valid Visa test number and appears in neither dict.
        self.assertNotIn("4111111111111111", APPROVE_CARDS)
        self.assertNotIn("4111111111111111", DECLINE_CARDS)
        charge = authorise(
            number="4111111111111111", cvc="123", amount="5.00", **FUTURE_EXP
        )
        self.assertEqual(charge.brand, "visa")


class AuthoriseDeclinedCardsTests(SimpleTestCase):
    """Every card the README's table promises will fail, actually does — with
    the matching machine-readable decline_code the checkout form depends on."""

    def test_every_documented_decline_card_raises_with_its_code(self):
        for number, (expected_code, expected_message) in DECLINE_CARDS.items():
            with self.subTest(number=number):
                with self.assertRaises(PaymentDeclined) as ctx:
                    authorise(number=number, cvc="123", amount="20.00", **FUTURE_EXP)
                self.assertEqual(ctx.exception.decline_code, expected_code)
                self.assertEqual(str(ctx.exception.detail), expected_message)

    def test_declined_response_uses_402_not_400(self):
        # 402 Payment Required distinguishes "the form was fine, the card
        # said no" from 400 "you typed something invalid" — the SPA branches
        # on this to decide whether to offer "try a different card" or
        # highlight a field.
        with self.assertRaises(PaymentDeclined) as ctx:
            authorise(number="4000000000000002", cvc="123", amount="20.00", **FUTURE_EXP)
        self.assertEqual(ctx.exception.status_code, 402)

    def test_expired_card_not_on_the_decline_list_is_declined_as_expired(self):
        # 4242... is an approved number, but a past expiry must still refuse
        # it — the decline list and the expiry check are independent gates.
        with self.assertRaises(PaymentDeclined) as ctx:
            authorise(
                number="4242424242424242",
                exp_month=1,
                exp_year=2020,
                cvc="123",
                amount="20.00",
            )
        self.assertEqual(ctx.exception.decline_code, "expired_card")

    def test_wrong_length_cvc_is_declined_as_incorrect_cvc(self):
        with self.assertRaises(PaymentDeclined) as ctx:
            authorise(
                number="4242424242424242", cvc="12", amount="20.00", **FUTURE_EXP
            )
        self.assertEqual(ctx.exception.decline_code, "incorrect_cvc")

    def test_amex_requires_four_digit_cvc_not_three(self):
        with self.assertRaises(PaymentDeclined) as ctx:
            authorise(
                number="378282246310005", cvc="123", amount="20.00", **FUTURE_EXP
            )
        self.assertEqual(ctx.exception.decline_code, "incorrect_cvc")
