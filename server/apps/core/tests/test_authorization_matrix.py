"""
Integration tests — the authorisation matrix.

The assignment brief calls this out specifically: "that authorisation holds,
so an anonymous visitor, a member, a seller and an administrator each get the
status codes they should from every endpoint." The README's "Security and
correctness" section makes the same promise ("Deny by default... a forgotten
permission fails closed") and "Three roles" ("admin, merchant, member... the
permission a URL needs is obvious from the URL").

This suite is the regression test for that promise. Rather than one test per
endpoint scattered across four files, ENDPOINT_MATRIX is a single table of
(method, path, expected status per role) that every role is checked against
in one pass — so adding a fifth endpoint is a one-line change, and a
permission class that quietly changes from IsAdmin to IsAuthenticated shows
up as a failing row instead of a silent hole.

Four identically-shaped API clients represent the four audiences the store
actually has:
  anonymous  - no Authorization header at all
  member     - a signed-in shopper
  merchant   - an approved, active seller (role=merchant, an active Merchant
               row, an active Brand)
  admin      - role=admin

401 means "you are not signed in"; 403 means "you are signed in but this is
not for you". The matrix checks the exact code, not just "not 200", because
the difference is what lets the SPA tell "please log in" apart from "this
account cannot do that".
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import Role
from apps.catalog.models import Brand, Product
from apps.merchants.models import Merchant

pytestmark = pytest.mark.integration

User = get_user_model()


class AuthorizationMatrixTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = User.objects.create_user(
            email="member@example.com", password="Member-Pass1", role=Role.MEMBER
        )
        cls.admin = User.objects.create_superuser(
            email="admin@example.com", password="Admin-Pass1"
        )

        cls.brand = Brand.objects.create(name="Campus Threads", is_active=True)
        cls.merchant_record = Merchant.objects.create(
            name="Campus Threads Seller",
            email="seller@example.com",
            brand_name="Campus Threads",
            is_active=True,
            brand=cls.brand,
        )
        cls.merchant_user = User.objects.create_user(
            email="seller-login@example.com",
            password="Seller-Pass1",
            role=Role.MERCHANT,
            merchant=cls.merchant_record,
        )

        cls.product = Product.objects.create(
            sku="MTX-001", name="Matrix Product", price=Decimal("15.00"), quantity=5
        )

    def setUp(self):
        self.anonymous = APIClient()

        self.member_client = APIClient()
        self.member_client.force_authenticate(user=self.member)

        self.merchant_client = APIClient()
        self.merchant_client.force_authenticate(user=self.merchant_user)

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)

        self.clients_by_role = {
            "anonymous": self.anonymous,
            "member": self.member_client,
            "merchant": self.merchant_client,
            "admin": self.admin_client,
        }

    def test_endpoint_matrix(self):
        # (method, path, expected status for anonymous/member/merchant/admin)
        matrix = [
            ("get", "/api/products/", {"anonymous": 200, "member": 200, "merchant": 200, "admin": 200}),
            ("get", "/api/categories/", {"anonymous": 200, "member": 200, "merchant": 200, "admin": 200}),
            ("get", "/api/brands/", {"anonymous": 200, "member": 200, "merchant": 200, "admin": 200}),
            (
                "get",
                f"/api/products/{self.product.slug}/",
                {"anonymous": 200, "member": 200, "merchant": 200, "admin": 200},
            ),
            # Owner-scoped: everyone signed in gets 200 (their own, possibly
            # empty, list); only anonymous is turned away at the door.
            ("get", "/api/orders/", {"anonymous": 401, "member": 200, "merchant": 200, "admin": 200}),
            ("get", "/api/users/me/", {"anonymous": 401, "member": 200, "merchant": 200, "admin": 200}),
            ("get", "/api/addresses/", {"anonymous": 401, "member": 200, "merchant": 200, "admin": 200}),
            ("get", "/api/wishlist/", {"anonymous": 401, "member": 200, "merchant": 200, "admin": 200}),
            # Admin-only user directory: everyone except admin is refused,
            # and refused for the *right* reason (401 vs 403).
            ("get", "/api/users/", {"anonymous": 401, "member": 403, "merchant": 403, "admin": 200}),
            # /api/manage/ - a merchant may reach product/brand CRUD (scoped
            # to their own brand elsewhere), never categories/merchants/reviews.
            ("get", "/api/manage/products/", {"anonymous": 401, "member": 403, "merchant": 200, "admin": 200}),
            ("get", "/api/manage/brands/", {"anonymous": 401, "member": 403, "merchant": 200, "admin": 200}),
            ("get", "/api/manage/categories/", {"anonymous": 401, "member": 403, "merchant": 403, "admin": 200}),
            ("get", "/api/manage/merchants/", {"anonymous": 401, "member": 403, "merchant": 403, "admin": 200}),
            ("get", "/api/manage/reviews/", {"anonymous": 401, "member": 403, "merchant": 403, "admin": 200}),
        ]

        for method, path, expected_by_role in matrix:
            for role, expected_status in expected_by_role.items():
                with self.subTest(method=method.upper(), path=path, role=role):
                    client = self.clients_by_role[role]
                    response = getattr(client, method)(path)
                    self.assertEqual(
                        response.status_code,
                        expected_status,
                        (
                            f"{role} -> {method.upper()} {path}: expected "
                            f"{expected_status}, got {response.status_code}"
                        ),
                    )

    def test_a_deactivated_merchant_loses_manage_access_but_keeps_the_role(self):
        # apps/core/permissions.py:IsMerchant checks merchant.is_active, not
        # just user.role — a withdrawn approval must close the door even
        # though the account still has role="merchant".
        self.merchant_record.is_active = False
        self.merchant_record.save(update_fields=["is_active"])

        response = self.merchant_client.get("/api/manage/products/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.merchant_user.role, Role.MERCHANT)  # role itself is untouched

    def test_a_member_cannot_read_another_members_address_by_guessing_its_id(self):
        from apps.accounts.models import Address

        other_member = User.objects.create_user(
            email="other@example.com", password="Other-Pass1"
        )
        address = Address.objects.create(
            user=other_member,
            address="1 Someone Else St",
            city="Melbourne",
            state="VIC",
            country="Australia",
            zip_code="3000",
        )

        response = self.member_client.get(f"/api/addresses/{address.id}/")
        # Scoped queryset means the row is simply not there - 404, not 403,
        # so the endpoint cannot be used to confirm the id exists at all.
        self.assertEqual(response.status_code, 404)

    def test_a_merchant_cannot_see_another_merchants_product_by_guessing_its_id(self):
        other_brand = Brand.objects.create(name="Someone Else's Brand", is_active=True)
        other_product = Product.objects.create(
            sku="OTH-001", name="Not Yours", price=Decimal("10.00"), quantity=1, brand=other_brand
        )
        response = self.merchant_client.get(f"/api/manage/products/{other_product.id}/")
        self.assertEqual(response.status_code, 404)

    def test_forgetting_to_send_a_token_is_401_not_403(self):
        # A blanket smoke check that DRF's DEFAULT_PERMISSION_CLASSES is
        # still IsAuthenticated - i.e. a brand new endpoint with no explicit
        # permission_classes fails closed rather than open.
        response = self.anonymous.get("/api/orders/")
        self.assertEqual(response.status_code, 401)
