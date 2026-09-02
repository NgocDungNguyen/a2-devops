"""
Unit tests — server-side money math (apps/orders/services.py: money(), tax_for()).

`money()` and `tax_for()` are pure Decimal functions with no database access,
which is what makes them safe to pin down in isolation from the checkout
transaction that calls them (see test_checkout_integration.py for the
end-to-end version, including the stock decrement).

The numbers in TaxForTests reproduce, digit for digit, the worked example in
the README's "Verifying a deployment -> Journey B":

    One taxable line at $44.95 and one non-taxable at $27.95: subtotal
    $72.90, tax $2.25 - five per cent of the t-shirt alone, not of the
    subtotal - and a total of $75.15.

If `money()`'s rounding mode ever changes, or `tax_for()` starts taxing the
subtotal instead of the line, this suite fails before a shopper's receipt
does.
"""

from decimal import Decimal

import pytest
from django.test import SimpleTestCase, override_settings

from apps.orders.services import money, tax_for

pytestmark = pytest.mark.unit


class MoneyRoundingTests(SimpleTestCase):
    """Round to cents, half up — the way a till does it."""

    def test_rounds_down_below_the_halfway_point(self):
        self.assertEqual(money(Decimal("10.004")), Decimal("10.00"))

    def test_rounds_up_at_the_halfway_point(self):
        # ROUND_HALF_UP, not banker's rounding: 10.005 always rounds away
        # from zero, never down to 10.00 depending on parity.
        self.assertEqual(money(Decimal("10.005")), Decimal("10.01"))

    def test_rounds_up_above_the_halfway_point(self):
        self.assertEqual(money(Decimal("10.006")), Decimal("10.01"))

    def test_already_exact_cents_are_unchanged(self):
        self.assertEqual(money(Decimal("19.99")), Decimal("19.99"))

    def test_accepts_a_plain_string(self):
        # The call sites in services.py sometimes pass strings straight from
        # request data; money() must not require the caller to pre-convert.
        self.assertEqual(money("5"), Decimal("5.00"))

    def test_zero_stays_zero(self):
        self.assertEqual(money(Decimal("0")), Decimal("0.00"))


@override_settings(SALES_TAX_RATE=0.05)
class TaxForTests(SimpleTestCase):
    """Sales tax applies only to a line flagged taxable, at a flat rate."""

    def test_non_taxable_line_owes_no_tax(self):
        self.assertEqual(tax_for(Decimal("27.95"), taxable=False), Decimal("0.00"))

    def test_taxable_line_matches_the_readme_worked_example(self):
        # 44.95 * 0.05 = 2.2475, which rounds up to 2.25 — the exact figure
        # the README's screenshot of a real checkout shows.
        self.assertEqual(tax_for(Decimal("44.95"), taxable=True), Decimal("2.25"))

    def test_a_second_taxable_line_added_to_the_first_matches_the_total(self):
        subtotal = Decimal("44.95") + Decimal("27.95")
        tax = tax_for(Decimal("44.95"), taxable=True) + tax_for(
            Decimal("27.95"), taxable=False
        )
        total = subtotal + tax
        self.assertEqual(subtotal, Decimal("72.90"))
        self.assertEqual(tax, Decimal("2.25"))
        self.assertEqual(total, Decimal("75.15"))

    def test_zero_amount_owes_zero_tax_even_if_taxable(self):
        self.assertEqual(tax_for(Decimal("0.00"), taxable=True), Decimal("0.00"))

    @override_settings(SALES_TAX_RATE=0.1)
    def test_tax_rate_is_read_from_settings_not_hard_coded(self):
        # Proves tax_for() is not silently pinned to 5% — a store operator
        # changing SALES_TAX_RATE in the environment (see the README's
        # "Public runtime config" feature) must actually change the maths.
        self.assertEqual(tax_for(Decimal("100.00"), taxable=True), Decimal("10.00"))


class CartTotalCalculationTests(SimpleTestCase):
    """Multi-line, multi-quantity totals — the arithmetic a cart summary runs.

    These mirror what apps/orders/services.create_order() does per line
    (`unit = money(price); line_total = money(unit * quantity)`) without
    touching the database, so a rounding regression is caught here before it
    is chased through a full checkout request.
    """

    def test_quantity_multiplies_the_unit_price_before_rounding(self):
        unit = money(Decimal("19.99"))
        line_total = money(unit * 3)
        self.assertEqual(line_total, Decimal("59.97"))

    def test_a_price_with_three_decimal_places_is_rounded_before_multiplying(self):
        # Guards the order of operations in create_order(): the unit price is
        # rounded to cents first, *then* multiplied by quantity - rounding
        # only the final line total can drift by a cent over enough units.
        unit = money(Decimal("0.335"))  # -> 0.34
        line_total = money(unit * 100)
        self.assertEqual(line_total, Decimal("34.00"))

    @override_settings(SALES_TAX_RATE=0.05)
    def test_bag_of_two_different_products_sums_correctly(self):
        lines = [
            (Decimal("44.95"), 1, True),
            (Decimal("27.95"), 1, False),
        ]
        subtotal = Decimal("0.00")
        total_tax = Decimal("0.00")
        for price, quantity, taxable in lines:
            line_total = money(money(price) * quantity)
            subtotal += line_total
            total_tax += tax_for(line_total, taxable)
        self.assertEqual(subtotal, Decimal("72.90"))
        self.assertEqual(total_tax, Decimal("2.25"))
        self.assertEqual(subtotal + total_tax, Decimal("75.15"))
