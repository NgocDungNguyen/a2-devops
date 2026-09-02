"""
Integration tests — checkout end to end (API -> service layer -> database).

Unlike test_payments_unit.py and test_pricing_unit.py, every test here goes
through the real HTTP layer (`self.client.post("/api/orders/", ...)`), the
real service function (`apps.orders.services.create_order`), and a real
database transaction. This is the suite the assignment brief singles out
by name: "that placing an order decrements stock and computes the total
server-side" and "that a declined card leaves no order behind and takes no
stock".

Why that matters more here than almost anywhere else in the codebase: this
is the one place money and inventory move together. A bug that decrements
stock on a declined payment empties a shelf for nothing; a bug that charges
a card without decrementing stock oversells it. Both are the kind of defect
that a manual click-through of the demo store is unlikely to catch, because
the happy path (successful payment, everything decrements once) looks
identical either way until you check the numbers.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.orders.models import Order, OrderItem
from apps.catalog.models import Product

pytestmark = pytest.mark.integration

User = get_user_model()

APPROVED_CARD = "4242424242424242"
DECLINED_CARD = "4000000000000002"  # -> decline_code "card_declined"


def _card(number=APPROVED_CARD, **overrides):
    payload = {
        "number": number,
        "exp_month": 12,
        "exp_year": 2099,
        "cvc": "123",
        "name_on_card": "Demo Member",
    }
    payload.update(overrides)
    return payload


class CheckoutIntegrationTestCase(APITestCase):
    """Shared fixtures for every test below: one signed-in member and two
    products whose prices are lifted straight from the README's worked
    example, so a passing test doubles as proof the documented example is
    accurate."""

    def setUp(self):
        self.member = User.objects.create_user(
            email="shopper@example.com", password="Sh0pper-Pass!"
        )
        self.client.force_authenticate(user=self.member)

        self.taxable_product = Product.objects.create(
            sku="TEE-001",
            name="RMIT Taxable Tee",
            price=Decimal("44.95"),
            taxable=True,
            quantity=10,
            is_active=True,
        )
        self.exempt_product = Product.objects.create(
            sku="MUG-001",
            name="RMIT Exempt Mug",
            price=Decimal("27.95"),
            taxable=False,
            quantity=5,
            is_active=True,
        )

    def _checkout(self, items, card=None):
        return self.client.post(
            "/api/orders/",
            {"items": items, "payment": card or _card()},
            format="json",
        )


class SuccessfulCheckoutTests(CheckoutIntegrationTestCase):
    def test_order_is_created_with_server_computed_totals(self):
        response = self._checkout(
            [
                {"product": self.taxable_product.id, "quantity": 1},
                {"product": self.exempt_product.id, "quantity": 1},
            ]
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        # Figures match the README's Journey B screenshot exactly.
        self.assertEqual(Decimal(response.data["subtotal"]), Decimal("72.90"))
        self.assertEqual(Decimal(response.data["total_tax"]), Decimal("2.25"))
        self.assertEqual(Decimal(response.data["total"]), Decimal("75.15"))
        self.assertEqual(response.data["payment_status"], "paid")
        self.assertEqual(response.data["card_last4"], "4242")
        self.assertEqual(response.data["card_brand"], "visa")

    def test_the_client_cannot_override_the_price_the_server_computes(self):
        # OrderCreateSerializer has no price/total field at all, so smuggling
        # one in is simply ignored rather than trusted — this is the
        # regression test for "the original took the total from the request
        # body and stored it without checking."
        response = self.client.post(
            "/api/orders/",
            {
                "items": [{"product": self.exempt_product.id, "quantity": 1}],
                "payment": _card(),
                "total": "0.01",
                "subtotal": "0.01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Decimal(response.data["total"]), Decimal("27.95"))

    def test_stock_is_decremented_by_exactly_the_purchased_quantity(self):
        self._checkout([{"product": self.taxable_product.id, "quantity": 3}])

        self.taxable_product.refresh_from_db()
        self.assertEqual(self.taxable_product.quantity, 7)  # 10 - 3

    def test_stock_decrements_once_even_when_a_product_is_listed_twice(self):
        # create_order() collapses duplicate lines for the same product
        # before checking or decrementing stock — assert it does not
        # decrement once per line.
        response = self._checkout(
            [
                {"product": self.taxable_product.id, "quantity": 1},
                {"product": self.taxable_product.id, "quantity": 2},
            ]
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        self.taxable_product.refresh_from_db()
        self.assertEqual(self.taxable_product.quantity, 7)  # 10 - (1 + 2), once
        self.assertEqual(OrderItem.objects.filter(order_id=response.data["id"]).count(), 1)
        self.assertEqual(
            OrderItem.objects.get(order_id=response.data["id"]).quantity, 3
        )

    def test_order_item_snapshots_survive_a_later_price_change(self):
        response = self._checkout([{"product": self.taxable_product.id, "quantity": 1}])
        order_id = response.data["id"]

        self.taxable_product.price = Decimal("999.00")
        self.taxable_product.name = "Renamed Product"
        self.taxable_product.save(update_fields=["price", "name"])

        detail = self.client.get(f"/api/orders/{order_id}/")
        line = detail.data["items"][0]
        self.assertEqual(line["product_name"], "RMIT Taxable Tee")
        self.assertEqual(Decimal(line["purchase_price"]), Decimal("44.95"))

    def test_exactly_one_order_and_one_line_item_are_created(self):
        self._checkout([{"product": self.exempt_product.id, "quantity": 1}])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)


class DeclinedCheckoutTests(CheckoutIntegrationTestCase):
    """A declined card must leave the database exactly as it found it."""

    def test_declined_card_returns_402_with_a_decline_code(self):
        response = self._checkout(
            [{"product": self.taxable_product.id, "quantity": 1}],
            card=_card(DECLINED_CARD),
        )
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertEqual(response.data["decline_code"], "card_declined")

    def test_declined_card_creates_no_order(self):
        self._checkout(
            [{"product": self.taxable_product.id, "quantity": 1}],
            card=_card(DECLINED_CARD),
        )
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_declined_card_takes_no_stock(self):
        self._checkout(
            [{"product": self.taxable_product.id, "quantity": 4}],
            card=_card(DECLINED_CARD),
        )
        self.taxable_product.refresh_from_db()
        self.assertEqual(self.taxable_product.quantity, 10)  # unchanged

    def test_every_documented_decline_reason_takes_no_stock(self):
        decline_cards = {
            "4000000000000002": "card_declined",
            "4000000000009995": "insufficient_funds",
            "4000000000000069": "expired_card",
            "4000000000000127": "incorrect_cvc",
            "4000000000000119": "processing_error",
        }
        for number, expected_code in decline_cards.items():
            with self.subTest(number=number):
                before = Product.objects.get(pk=self.taxable_product.pk).quantity
                response = self._checkout(
                    [{"product": self.taxable_product.id, "quantity": 1}],
                    card=_card(number),
                )
                self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
                self.assertEqual(response.data["decline_code"], expected_code)
                after = Product.objects.get(pk=self.taxable_product.pk).quantity
                self.assertEqual(before, after)
        self.assertEqual(Order.objects.count(), 0)


class StockAndValidationTests(CheckoutIntegrationTestCase):
    def test_ordering_more_than_is_in_stock_is_rejected_without_charging(self):
        low_stock = Product.objects.create(
            sku="LOW-001", name="Nearly Sold Out", price=Decimal("10.00"), quantity=1
        )
        response = self._checkout([{"product": low_stock.id, "quantity": 2}])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
        low_stock.refresh_from_db()
        self.assertEqual(low_stock.quantity, 1)  # untouched

    def test_an_inactive_product_cannot_be_bought(self):
        withdrawn = Product.objects.create(
            sku="OLD-001",
            name="Withdrawn Product",
            price=Decimal("10.00"),
            quantity=5,
            is_active=False,
        )
        response = self._checkout([{"product": withdrawn.id, "quantity": 1}])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_an_empty_bag_is_rejected(self):
        response = self._checkout([])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_a_nonexistent_product_id_is_rejected(self):
        response = self._checkout([{"product": 999999, "quantity": 1}])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_an_invalid_card_number_never_reaches_the_gateway(self):
        # Fails Luhn at the serializer, before payments.authorise() is ever
        # called - a 400, not a 402.
        response = self._checkout(
            [{"product": self.exempt_product.id, "quantity": 1}],
            card=_card("1234567890123456"),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)


class CheckoutAuthenticationTests(CheckoutIntegrationTestCase):
    def test_anonymous_visitor_cannot_check_out(self):
        self.client.force_authenticate(user=None)
        response = self._checkout([{"product": self.exempt_product.id, "quantity": 1}])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Order.objects.count(), 0)


class CancellationRestocksTests(CheckoutIntegrationTestCase):
    """The other half of the inventory story: cancelling gives stock back."""

    def test_cancelling_the_only_item_restocks_and_marks_the_order_cancelled(self):
        placed = self._checkout([{"product": self.taxable_product.id, "quantity": 2}])
        order_id = placed.data["id"]
        item_id = placed.data["items"][0]["id"]

        response = self.client.patch(
            f"/api/orders/{order_id}/items/{item_id}/", {"status": "cancelled"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")
        self.assertEqual(response.data["payment_status"], "refunded")

        self.taxable_product.refresh_from_db()
        self.assertEqual(self.taxable_product.quantity, 10)  # back to the starting stock

    def test_a_member_cannot_move_an_item_to_a_fulfilment_status(self):
        # Only "cancelled" is available to the customer; "shipped" etc. is
        # the store's call, not the shopper's.
        placed = self._checkout([{"product": self.taxable_product.id, "quantity": 1}])
        order_id = placed.data["id"]
        item_id = placed.data["items"][0]["id"]

        response = self.client.patch(
            f"/api/orders/{order_id}/items/{item_id}/", {"status": "shipped"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_an_admin_can_move_an_item_through_fulfilment_without_touching_stock(self):
        admin = User.objects.create_superuser(
            email="admin@example.com", password="Adm1n-Pass!"
        )
        placed = self._checkout([{"product": self.taxable_product.id, "quantity": 1}])
        order_id = placed.data["id"]
        item_id = placed.data["items"][0]["id"]

        self.client.force_authenticate(user=admin)
        response = self.client.patch(
            f"/api/orders/{order_id}/items/{item_id}/", {"status": "shipped"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"][0]["status"], "shipped")

        self.taxable_product.refresh_from_db()
        self.assertEqual(self.taxable_product.quantity, 9)  # unaffected by fulfilment
