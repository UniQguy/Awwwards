"""
Tests for Inventory and Stock Reservation service.
Tests concurrency, idempotency, TTL expiration, and atomic decrements.
"""

from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.inventory.exceptions import (
    InsufficientStockError,
    InvalidReservationStateError,
    ReservationExpiredError,
)
from apps.inventory.models import Inventory, StockReservation
from apps.inventory.services.reservation_service import (
    cleanup_expired_reservations,
    convert_reservation,
    extend_reservation,
    get_available_stock,
    release_reservation,
    reserve_stock,
)


class InventoryReservationServiceTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(
            name="Audio",
            slug="audio-inv",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
        )
        self.prod = Product.objects.create(
            category=self.cat,
            sku="EC-TEST-INV-1",
            slug="ec-test-inv-1",
            raw_name="Audio Pro Headphones",
            display_name="Audio Pro Headphones",
            source_asin="B000TESTINV1",
            selling_price=Decimal("4999.00"),
            is_available=True,
        )
        self.inventory = Inventory.objects.create(
            product=self.prod,
            quantity=10,
            low_stock_threshold=3,
        )

    def test_available_stock_initial(self):
        self.assertEqual(get_available_stock(self.prod), 10)

    def test_reserve_stock_reduces_available(self):
        res = reserve_stock(self.prod, quantity=3, owner_key="guest_sess_1")
        self.assertEqual(res.quantity, 3)
        self.assertEqual(res.status, StockReservation.STATUS_RESERVED)
        self.assertEqual(get_available_stock(self.prod), 7)

    def test_reserve_excess_stock_fails(self):
        with self.assertRaises(InsufficientStockError) as ctx:
            reserve_stock(self.prod, quantity=15, owner_key="guest_sess_2")
        self.assertEqual(ctx.exception.requested, 15)
        self.assertEqual(ctx.exception.available, 10)

    def test_reservation_idempotency_same_owner(self):
        res1 = reserve_stock(self.prod, quantity=2, owner_key="guest_sess_idem")
        self.assertEqual(get_available_stock(self.prod), 8)

        # Calling again for same owner updates quantity
        res2 = reserve_stock(self.prod, quantity=4, owner_key="guest_sess_idem")
        self.assertEqual(res1.id, res2.id)
        self.assertEqual(res2.quantity, 4)
        self.assertEqual(get_available_stock(self.prod), 6)

    def test_extend_reservation(self):
        res = reserve_stock(self.prod, quantity=2, owner_key="guest_sess_ext", ttl_minutes=15)
        old_exp = res.expires_at
        extended = extend_reservation(res, minutes=45)
        self.assertGreater(extended.expires_at, old_exp)
        self.assertIsNotNone(extended.extended_at)

    def test_convert_reservation_decrements_inventory(self):
        res = reserve_stock(self.prod, quantity=4, owner_key="guest_sess_conv")
        convert_reservation(res)

        res.refresh_from_db()
        self.assertEqual(res.status, StockReservation.STATUS_CONVERTED)

        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 6)
        self.assertEqual(get_available_stock(self.prod), 6)

    def test_release_reservation(self):
        res = reserve_stock(self.prod, quantity=4, owner_key="guest_sess_rel")
        self.assertEqual(get_available_stock(self.prod), 6)

        release_reservation(res)
        res.refresh_from_db()
        self.assertEqual(res.status, StockReservation.STATUS_RELEASED)
        self.assertEqual(get_available_stock(self.prod), 10)

    def test_cleanup_expired_reservations(self):
        # Create an expired reservation directly
        past = timezone.now() - timedelta(minutes=5)
        StockReservation.objects.create(
            product=self.prod,
            owner_key="expired_guest",
            quantity=3,
            status=StockReservation.STATUS_RESERVED,
            expires_at=past,
        )
        # Because it's expired, get_available_stock ignores it
        self.assertEqual(get_available_stock(self.prod), 10)

        cleaned = cleanup_expired_reservations()
        self.assertEqual(cleaned, 1)

    def test_converting_expired_reservation_raises(self):
        past = timezone.now() - timedelta(minutes=5)
        res = StockReservation.objects.create(
            product=self.prod,
            owner_key="expired_guest",
            quantity=3,
            status=StockReservation.STATUS_RESERVED,
            expires_at=past,
        )
        with self.assertRaises(ReservationExpiredError):
            convert_reservation(res)


class InventoryConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.cat = Category.objects.create(
            name="Phones",
            slug="phones-conc",
            accent_key="smartphones",
            gst_rate=Decimal("18.00"),
        )
        self.prod = Product.objects.create(
            category=self.cat,
            sku="EC-CONC-PROD-1",
            slug="ec-conc-prod-1",
            raw_name="Limited Phone",
            display_name="Limited Phone",
            source_asin="B00CONCUR001",
            selling_price=Decimal("19999.00"),
            is_available=True,
        )
        self.inventory = Inventory.objects.create(
            product=self.prod,
            quantity=5,
        )

    def test_serial_reservations_drain_stock_correctly(self):
        res1 = reserve_stock(self.prod, quantity=3, owner_key="user_1")
        res2 = reserve_stock(self.prod, quantity=2, owner_key="user_2")
        self.assertEqual(get_available_stock(self.prod), 0)

        with self.assertRaises(InsufficientStockError):
            reserve_stock(self.prod, quantity=1, owner_key="user_3")
