"""
Tests for Order placement, gap-free Invoicing, Credit Notes, and Status Transitions.
"""

from datetime import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory, StockReservation
from apps.inventory.services.reservation_service import get_available_stock
from apps.cart.models import Cart
from apps.cart.services.cart_service import add_to_cart, get_or_create_cart
from apps.orders.models import CreditNote, Invoice, Order, OrderItem
from apps.orders.services.invoicing import (
    generate_credit_note,
    generate_invoice,
    get_financial_year,
)
from apps.orders.services.order_creator import place_order
from apps.orders.services.order_status import (
    InvalidOrderTransitionError,
    transition_order_status,
)
from apps.orders.services.tracking import get_tracking_info

User = get_user_model()


class InvoicingFinancialYearAndSequenceTests(TestCase):
    def test_financial_year_boundaries(self):
        # In India, April starts new FY
        dt_oct = datetime(2026, 10, 15)
        self.assertEqual(get_financial_year(dt_oct), "2026-27")

        dt_jan = datetime(2027, 1, 10)
        self.assertEqual(get_financial_year(dt_jan), "2026-27")

        dt_mar = datetime(2027, 3, 31)
        self.assertEqual(get_financial_year(dt_mar), "2026-27")

        dt_apr = datetime(2027, 4, 1)
        self.assertEqual(get_financial_year(dt_apr), "2027-28")


class OrderPlacementAndLifecycleTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(
            name="Audio",
            slug="earphones-headphones",
            accent_key="earphones-headphones",
            hsn_code="8518",
            gst_rate=Decimal("18.00"),
            is_gst_rate_verified=True,
        )
        self.prod = Product.objects.create(
            category=self.cat,
            sku="EC-ORDER-PROD-1",
            slug="ec-order-prod-1",
            raw_name="Hi-Res Studio Headphones",
            display_name="Hi-Res Headphones",
            source_asin="B00ORD0001",
            selling_price=Decimal("4999.00"),
            mrp=Decimal("6999.00"),
            is_available=True,
        )
        self.inventory = Inventory.objects.create(
            product=self.prod,
            quantity=10,
        )
        self.user = User.objects.create_user(email="buyer@example.com", password="SecurePassword123!")
        self.cart = get_or_create_cart(user=self.user)

    def test_place_cod_order_auto_converts_and_invoices(self):
        add_to_cart(self.cart, self.prod, quantity=2)

        shipping_addr = {
            "street": "123 Indiranagar 100ft Road",
            "city": "Ahmedabad",
            "state": "KA",
            "pincode": "560038",
            "phone": "9876543210",
        }

        order = place_order(
            cart=self.cart,
            user=self.user,
            shipping_address=shipping_addr,
            payment_method="cod",
        )

        self.assertEqual(order.status, Order.STATUS_CONFIRMED)
        self.assertEqual(order.payment_method, "cod")
        self.assertEqual(order.items.count(), 1)

        # Inventory check: 10 - 2 = 8
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 8)
        self.assertEqual(get_available_stock(self.prod), 8)

        # Invoice check: sequential gap-free invoice issued
        self.assertTrue(hasattr(order, "invoice"))
        inv = order.invoice
        self.assertTrue(inv.invoice_number.startswith("EC-INV-"))
        self.assertEqual(inv.sequence_number, 1)

        # Cart should be cleared
        self.assertEqual(self.cart.items.count(), 0)

    def test_place_razorpay_order_leaves_pending(self):
        add_to_cart(self.cart, self.prod, quantity=1)

        shipping_addr = {
            "street": "456 Bandra West",
            "city": "Mumbai",
            "state": "MH",
            "pincode": "400050",
            "phone": "9876543211",
        }

        order = place_order(
            cart=self.cart,
            user=self.user,
            shipping_address=shipping_addr,
            payment_method="razorpay",
        )

        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertEqual(order.payment_method, "razorpay")

        # Physical inventory not decremented yet, but reservation active
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 10)
        self.assertEqual(get_available_stock(self.prod), 9)

        # No invoice until captured
        self.assertFalse(hasattr(order, "invoice") and order.invoice is not None)

    def test_snapshot_immutability(self):
        add_to_cart(self.cart, self.prod, quantity=1)
        shipping_addr = {"state": "KA", "pincode": "560001"}
        order = place_order(self.cart, user=self.user, shipping_address=shipping_addr, payment_method="cod")

        item = order.items.first()
        self.assertEqual(item.unit_price, Decimal("4999.00"))

        # Alter original catalog product
        self.prod.selling_price = Decimal("8999.00")
        self.prod.save()

        # OrderItem snapshot remains untouched
        item.refresh_from_db()
        self.assertEqual(item.unit_price, Decimal("4999.00"))

    def test_status_transitions_and_cancellation_restock(self):
        add_to_cart(self.cart, self.prod, quantity=2)
        shipping_addr = {"state": "KA", "pincode": "560001"}
        order = place_order(self.cart, user=self.user, shipping_address=shipping_addr, payment_method="cod")
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 8)

        # Transition confirmed -> processing
        transition_order_status(order, Order.STATUS_PROCESSING, notes="Preparing packaging")
        self.assertEqual(order.status, Order.STATUS_PROCESSING)

        # Invalid transition: processing -> delivered (skipping shipped)
        with self.assertRaises(InvalidOrderTransitionError):
            transition_order_status(order, Order.STATUS_DELIVERED)

        # Cancellation while processing: must restock and issue Credit Note
        transition_order_status(order, Order.STATUS_CANCELLED, notes="Customer changed mind")
        self.assertEqual(order.status, Order.STATUS_CANCELLED)

        # Stock is restocked to 10
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 10)

        # Credit note issued
        cn = CreditNote.objects.filter(order=order).first()
        self.assertIsNotNone(cn)
        self.assertTrue(cn.credit_note_number.startswith("EC-CN-"))
        self.assertEqual(cn.amount, order.total_amount)

    def test_tracking_service(self):
        add_to_cart(self.cart, self.prod, quantity=1)
        shipping_addr = {"state": "KA", "pincode": "560001"}
        order = place_order(self.cart, user=self.user, shipping_address=shipping_addr, payment_method="cod")

        info = get_tracking_info(order)
        self.assertEqual(info["order_number"], order.order_number)
        self.assertFalse(info["is_delivered"])
        self.assertEqual(len(info["steps"]), 4)
