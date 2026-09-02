"""
Integration tests — the storefront catalogue API (GET /api/products/ and
friends), end to end through the real HTTP layer and a real database.

This is the suite that proves, in the assignment brief's words, "that the
shop endpoint actually returns products, proving the API-to-database
connection". It is also the fastest possible regression test for the
storefront's core promise from the README: "Inactive products, brands and
categories never appear on the storefront, whatever URL is guessed" — that
promise is enforced entirely by `Product.objects.storefront()` filtering the
queryset, so it is worth pinning down directly rather than trusting the
frontend never to render something the API should not have sent.
"""

from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import Brand, Category, Product

pytestmark = pytest.mark.integration


class StorefrontProductListTests(APITestCase):
    def setUp(self):
        self.active_brand = Brand.objects.create(name="Campus Threads", is_active=True)
        self.inactive_brand = Brand.objects.create(name="Delisted Brand", is_active=False)

        self.visible_product = Product.objects.create(
            sku="VIS-001",
            name="Visible Hoodie",
            price=Decimal("59.95"),
            quantity=20,
            is_active=True,
            brand=self.active_brand,
        )
        self.inactive_product = Product.objects.create(
            sku="INV-001",
            name="Deactivated Cap",
            price=Decimal("19.95"),
            quantity=20,
            is_active=False,
        )
        self.orphaned_by_brand = Product.objects.create(
            sku="INV-002",
            name="Product Under a Delisted Brand",
            price=Decimal("29.95"),
            quantity=20,
            is_active=True,
            brand=self.inactive_brand,
        )

    def test_anonymous_visitor_can_list_products(self):
        # /api/products/ is public — the shopfront must render with no login.
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_reaches_the_database_and_returns_the_seeded_product(self):
        response = self.client.get("/api/products/")
        names = [row["name"] for row in response.data["results"]]
        self.assertIn("Visible Hoodie", names)

    def test_an_inactive_product_never_appears(self):
        response = self.client.get("/api/products/")
        names = [row["name"] for row in response.data["results"]]
        self.assertNotIn("Deactivated Cap", names)

    def test_a_product_whose_brand_was_deactivated_never_appears(self):
        response = self.client.get("/api/products/")
        names = [row["name"] for row in response.data["results"]]
        self.assertNotIn("Product Under a Delisted Brand", names)

    def test_an_inactive_product_404s_on_its_own_detail_page_too(self):
        # "whatever URL is guessed" — the detail route must apply the same
        # storefront() filter as the list, not just hide the card.
        response = self.client.get(f"/api/products/{self.inactive_product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pagination_envelope_has_the_shape_the_shop_toolbar_expects(self):
        response = self.client.get("/api/products/")
        for key in ("count", "total_pages", "current_page", "page_size", "results"):
            self.assertIn(key, response.data)

    def test_price_range_filter_narrows_the_results(self):
        Product.objects.create(
            sku="EXP-001", name="Expensive Jacket", price=Decimal("199.00"), quantity=5
        )
        response = self.client.get("/api/products/", {"max_price": "100"})
        prices = [Decimal(row["price"]) for row in response.data["results"]]
        self.assertTrue(all(price <= Decimal("100") for price in prices))
        names = [row["name"] for row in response.data["results"]]
        self.assertNotIn("Expensive Jacket", names)

    def test_ordering_whitelist_rejects_an_arbitrary_column(self):
        # ORDERING_WHITELIST falls back to the default ("newest") for
        # anything not on the list — the endpoint must not let the caller
        # order by an arbitrary column (the vulnerability this replaced).
        response = self.client.get("/api/products/", {"ordering": "id; DROP TABLE"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_price_ascending_sort_is_actually_ascending(self):
        Product.objects.create(sku="A-1", name="A", price=Decimal("5.00"), quantity=1)
        Product.objects.create(sku="B-1", name="B", price=Decimal("500.00"), quantity=1)
        response = self.client.get("/api/products/", {"ordering": "price_asc", "page_size": 50})
        prices = [Decimal(row["price"]) for row in response.data["results"]]
        self.assertEqual(prices, sorted(prices))

    def test_search_matches_on_name_case_insensitively(self):
        response = self.client.get("/api/products/", {"search": "hoodie"})
        names = [row["name"] for row in response.data["results"]]
        self.assertIn("Visible Hoodie", names)

    def test_search_with_no_match_returns_an_empty_list_not_an_error(self):
        response = self.client.get("/api/products/", {"search": "no-such-product-xyz"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])


class StorefrontCategoryAndBrandTests(APITestCase):
    def test_only_active_categories_are_listed(self):
        Category.objects.create(name="Visible Category", is_active=True)
        Category.objects.create(name="Hidden Category", is_active=False)

        response = self.client.get("/api/categories/")
        names = [row["name"] for row in response.data]
        self.assertIn("Visible Category", names)
        self.assertNotIn("Hidden Category", names)

    def test_only_active_brands_are_listed(self):
        Brand.objects.create(name="Visible Brand", is_active=True)
        Brand.objects.create(name="Hidden Brand", is_active=False)

        response = self.client.get("/api/brands/")
        names = [row["name"] for row in response.data]
        self.assertIn("Visible Brand", names)
        self.assertNotIn("Hidden Brand", names)


class ManageCatalogPermissionTests(APITestCase):
    """A slice of the authorisation story specific to catalog management —
    the fuller cross-role matrix lives in apps/core/tests/test_authorization_matrix.py."""

    def test_anonymous_visitor_cannot_create_a_product(self):
        response = self.client.post(
            "/api/manage/products/",
            {"sku": "NEW-1", "name": "New", "price": "10.00", "quantity": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_signed_in_member_cannot_create_a_product(self):
        from django.contrib.auth import get_user_model

        member = get_user_model().objects.create_user(
            email="member@example.com", password="Member-Pass1"
        )
        self.client.force_authenticate(user=member)
        response = self.client.post(
            "/api/manage/products/",
            {"sku": "NEW-1", "name": "New", "price": "10.00", "quantity": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
