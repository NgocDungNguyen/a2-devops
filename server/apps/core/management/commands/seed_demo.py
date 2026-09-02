"""
Populate the store with demo data.

    python manage.py seed_demo --admin-email admin@rmit.edu.au \
                               --admin-password 'RmitStore2767!' --demo-users

Replaces the `seed:db` script from the MERN app and keeps its shape: an admin
account plus categories, brands and products built from the 47 product
photographs in `seed_assets/products/`.

The catalogue itself lives in `_seed_catalog.py`, not here. Every product names
the photograph it belongs to, so the image, the name, the description and the
reviews all describe the same object - see that file for why that matters.

Three deliberate properties:

  * The random generator is seeded with a fixed value, so every student's
    catalogue is identical. That makes screenshots in the course material
    match what you see on screen, and makes it possible to assert on counts.
  * Reviews are generated, and are drawn from a pool chosen by product type.
    The original seeded none, so a fresh install had zero stars everywhere and
    the rating filter on the shop page looked broken.
  * Ratings are spread across one to five stars on purpose. A catalogue where
    everything scores five cannot be used to verify the "4 stars & up" filter
    or the sort.

The command is idempotent: run it twice and it will skip what already exists.
"""

import random
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Address, Role
from apps.catalog.models import Brand, Category, Product
from apps.merchants.models import Merchant, MerchantStatus
from apps.reviews.models import Review, ReviewStatus

from ._seed_catalog import (
    BRANDS,
    CATEGORIES,
    MERCHANT_PRODUCTS,
    PRODUCTS,
    REVIEWS_BY_KIND,
)

User = get_user_model()

SEED = 2767


class Command(BaseCommand):
    help = "Seed the database with an admin account and a demo catalogue."

    def add_arguments(self, parser):
        parser.add_argument("--admin-email", default="admin@rmit.edu.au")
        parser.add_argument("--admin-password", default=None)
        # The catalogue is curated rather than generated, so these are caps on
        # the curated lists rather than "how many to invent".
        parser.add_argument("--categories", type=int, default=len(CATEGORIES))
        parser.add_argument("--brands", type=int, default=len(BRANDS))
        parser.add_argument("--products", type=int, default=len(PRODUCTS))
        # Enough for every product to get three or four. Below roughly 3 x the
        # product count some products end up with none, and a product with no
        # stars at all makes the shop's rating filter look broken.
        parser.add_argument("--reviews", type=int, default=160)
        parser.add_argument(
            "--demo-users",
            action="store_true",
            help="Also create a demo member and an approved demo merchant.",
        )
        parser.add_argument(
            "--no-images",
            action="store_true",
            help="Skip attaching product photographs (much faster).",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete the existing catalogue, orders, reviews and sellers first.",
        )

    def handle(self, *args, **options):
        self.random = random.Random(SEED)
        # product pk -> the `kind` from the catalogue, so reviews can be drawn
        # from a pool that matches what the product actually is.
        self.product_kinds = {}

        if options["flush"]:
            self._flush()

        admin = self._create_admin(options["admin_email"], options["admin_password"])
        categories = self._create_categories(options["categories"])
        brands = self._create_brands(options["brands"])
        products = self._create_products(
            options["products"], brands, categories, use_images=not options["no_images"]
        )

        members = [admin]
        if options["demo_users"]:
            members += self._create_demo_users(
                categories, use_images=not options["no_images"]
            )
            products = list(Product.objects.all())

        self._create_reviews(options["reviews"], products, members)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seeding complete."))
        self.stdout.write(f"  Categories : {Category.objects.count()}")
        self.stdout.write(f"  Brands     : {Brand.objects.count()}")
        self.stdout.write(f"  Products   : {Product.objects.count()}")
        self.stdout.write(f"  Reviews    : {Review.objects.count()}")
        self.stdout.write(f"  Users      : {User.objects.count()}")
        self.stdout.write("")
        self.stdout.write(f"  Sign in as : {options['admin_email']}")

    # -- steps --------------------------------------------------------------

    @transaction.atomic
    def _flush(self):
        """Remove the catalogue, orders and seller records.

        Merchants go too. A merchant whose brand has been deleted is in a
        broken state - approved, but with nothing to sell under - so leaving
        them behind would mean --flush produced a database that could not be
        re-seeded cleanly.

        User accounts are kept: dropping them would sign you out of the admin
        site mid-session. Their merchant link is nulled by the foreign key.
        """
        from apps.orders.models import Order, OrderItem

        self.stdout.write(
            self.style.WARNING("Flushing catalogue, orders and seller records...")
        )
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Review.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Merchant.objects.all().update(brand=None)
        Merchant.objects.all().delete()
        Brand.objects.all().delete()

    def _create_admin(self, email, password):
        existing = User.objects.filter(email__iexact=email).first()
        if existing:
            self.stdout.write(f"Admin {email} already exists, skipping.")
            return existing

        if not password:
            raise CommandError(
                "--admin-password is required the first time you seed. Example:\n"
                "  python manage.py seed_demo --admin-email you@rmit.edu.au "
                "--admin-password 'RmitStore2767!'"
            )

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name="Store",
            last_name="Admin",
            role=Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Created admin {email}"))
        return user

    def _create_categories(self, target):
        """Create the curated categories, skipping any that already exist.

        Matching on name rather than counting means a half-seeded database
        gains the categories it is missing instead of being declared done.
        """
        existing = {c.name: c for c in Category.objects.all()}
        created = []
        for name, description in CATEGORIES[:target]:
            if name in existing:
                continue
            category = Category(name=name, description=description, is_active=True)
            category.save()  # save() individually so slugs are generated
            existing[name] = category
            created.append(category)

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created {len(created)} categories"))
        else:
            self.stdout.write(f"{len(existing)} categories already exist, skipping.")
        return existing

    def _create_brands(self, target):
        existing = {
            b.name: b for b in Brand.objects.filter(merchant__isnull=True)
        }
        created = []
        for name, description in BRANDS[:target]:
            if name in existing:
                continue
            brand = Brand(name=name, description=description, is_active=True)
            brand.save()
            existing[name] = brand
            created.append(brand)

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created {len(created)} brands"))
        else:
            self.stdout.write(f"{len(existing)} brands already exist, skipping.")
        return existing

    def _create_products(self, target, brands, categories, use_images=True):
        """Create the curated catalogue.

        Each entry carries its own photograph number, so a product's image is
        a property of the product rather than a draw from a shuffled pool.
        """
        existing = {p.sku: p for p in Product.objects.all()}
        products, created = [], []

        for entry in PRODUCTS[:target]:
            found = existing.get(entry["sku"])
            if found:
                products.append(found)
                self.product_kinds[found.pk] = entry["kind"]
                continue

            product = Product(
                sku=entry["sku"],
                name=entry["name"],
                description=entry["description"],
                quantity=entry["quantity"],
                price=Decimal(entry["price"]),
                taxable=entry["taxable"],
                is_active=True,
                brand=brands.get(entry["brand"]),
            )
            product.save()
            product.categories.set(
                [categories[name] for name in entry["categories"] if name in categories]
            )
            if use_images:
                self._attach_image(product, entry["image"])

            self.product_kinds[product.pk] = entry["kind"]
            products.append(product)
            created.append(product)
            if len(created) % 20 == 0:
                self.stdout.write(f"  ...{len(created)} products")

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created {len(created)} products"))
        else:
            self.stdout.write(f"{len(products)} products already exist, skipping.")
        return products

    def _attach_image(self, product, number):
        """Save a seed photograph through the configured storage backend.

        Going through the storage API rather than copying files means the same
        command works unchanged when USE_S3 is switched on - the seed data
        lands in the bucket alongside merchant uploads.
        """
        path = Path(settings.BASE_DIR) / "seed_assets" / "products" / f"p-{number}.jpg"
        if not path.exists():
            return
        with path.open("rb") as handle:
            product.image.save(f"p-{number}.jpg", File(handle), save=True)

    @transaction.atomic
    def _create_demo_users(self, categories, use_images=True):
        """A member and an approved merchant, so both journeys are testable.

        Without these, exercising the seller experience after every deploy
        means running the whole apply-approve-email-accept dance by hand.

        Note the passwords. set_password() bypasses AUTH_PASSWORD_VALIDATORS,
        so an obvious choice like "Member123!" would seed happily and then be
        rejected the moment somebody typed it into the change-password form -
        UserAttributeSimilarityValidator considers it too close to the last
        name. These values pass the same validators the application enforces,
        so the demo data and the application agree with each other.
        """
        created_users = []

        member, created = User.objects.get_or_create(
            email="member@rmit.edu.au",
            defaults={"first_name": "Demo", "last_name": "Member", "role": Role.MEMBER},
        )
        if created:
            member.set_password("DemoPass2767!")
            member.save()
            Address.objects.create(
                user=member,
                address="124 La Trobe Street",
                city="Melbourne",
                state="VIC",
                country="Australia",
                zip_code="3000",
                is_default=True,
            )
            self.stdout.write(self.style.SUCCESS("Created demo member member@rmit.edu.au"))
        created_users.append(member)

        # Repair rather than skip. Each piece is checked independently so a
        # partially-seeded database (or one that has just been flushed) ends up
        # in the same state as a fresh one.
        merchant_email = "merchant@rmit.edu.au"
        merchant, merchant_created = Merchant.objects.get_or_create(
            email=merchant_email,
            defaults={
                "name": "Demo Merchant",
                "phone_number": "+61 3 9925 2000",
                "brand_name": "Campus Threads",
                "business": "A student-run label printing sustainable RMIT apparel.",
                "status": MerchantStatus.APPROVED,
                "is_active": True,
            },
        )

        if merchant.brand_id is None:
            merchant.brand = Brand.objects.create(
                name="Campus Threads",
                description=merchant.business,
                # Active, unlike a real approval, so the demo seller's products
                # show up in the shop without an extra manual step.
                is_active=True,
            )
            merchant.save(update_fields=["brand", "updated_at"])

        merchant_user, _ = User.objects.get_or_create(
            email=merchant_email,
            defaults={"first_name": "Demo", "last_name": "Merchant"},
        )
        merchant_user.set_password("SellerPass2767!")
        merchant_user.role = Role.MERCHANT
        merchant_user.merchant = merchant
        merchant_user.save()
        created_users.append(merchant_user)

        # The seller's own products. These use the five photographs the main
        # catalogue deliberately leaves alone, so no two products in the shop
        # share an image.
        existing_skus = set(
            Product.objects.filter(sku__in=[e["sku"] for e in MERCHANT_PRODUCTS])
            .values_list("sku", flat=True)
        )
        for entry in MERCHANT_PRODUCTS:
            if entry["sku"] in existing_skus:
                continue
            product = Product(
                sku=entry["sku"],
                name=entry["name"],
                description=entry["description"],
                quantity=entry["quantity"],
                price=Decimal(entry["price"]),
                taxable=entry["taxable"],
                is_active=True,
                brand=merchant.brand,
            )
            product.save()
            product.categories.set(
                [categories[name] for name in entry["categories"] if name in categories]
            )
            if use_images:
                self._attach_image(product, entry["image"])
            self.product_kinds[product.pk] = entry["kind"]

        if merchant_created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created demo merchant {merchant_email} with "
                    f"{len(MERCHANT_PRODUCTS)} products"
                )
            )

        return created_users

    def _create_reviews(self, target, products, authors):
        """Write reviews that are about the product being reviewed.

        Each product gets its own shuffled copy of the review pool for its
        kind, and reviews are dealt round-robin across products. That spreads
        them over the catalogue instead of piling them onto the first few, and
        stops two products of the same kind opening with identical text.
        """
        if Review.objects.count() >= target:
            self.stdout.write("Reviews already exist, skipping.")
            return
        if not products or not authors:
            return

        order = [p for p in products if p.pk in self.product_kinds]
        if not order:
            return
        self.random.shuffle(order)

        # Per-product queue of candidate reviews, in a per-product order.
        queues = {}
        for product in order:
            pool = REVIEWS_BY_KIND.get(self.product_kinds[product.pk], [])
            queues[product.pk] = self.random.sample(list(pool), len(pool))

        created = 0
        exhausted = set()
        while created < target and len(exhausted) < len(order):
            for product in order:
                if created >= target:
                    break
                queue = queues[product.pk]
                if not queue:
                    exhausted.add(product.pk)
                    continue
                rating, title, body = queue.pop(0)
                Review.objects.create(
                    product=product,
                    user=self.random.choice(authors),
                    title=title,
                    rating=rating,
                    review=body,
                    is_recommended=rating >= 4,
                    status=ReviewStatus.APPROVED,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} reviews"))
