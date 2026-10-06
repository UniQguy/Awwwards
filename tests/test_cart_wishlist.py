"""
Tests for Cart, Wishlist, and Cart Financial Calculator.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.catalog.models import Category, Product
from apps.inventory.exceptions import InsufficientStockError
from apps.inventory.models import Inventory
from apps.cart.models import Cart, CartItem
from apps.cart.services.cart_calculator import calculate_cart_summary
from apps.cart.services.cart_service import (
    add_to_cart,
    clear_cart,
    get_or_create_cart,
    merge_carts,
    remove_from_cart,
    update_cart_quantity,
)
from apps.shipping.models import ShippingConfig
from apps.wishlist.models import Wishlist, WishlistItem
from apps.wishlist.services.wishlist_service import (
    get_or_create_wishlist,
    merge_wishlists,
    move_to_cart,
    toggle_wishlist,
)

User = get_user_model()


class CartAndWishlistTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(
            name="Audio",
            slug="audio-cart",
            accent_key="earphones-headphones",
            gst_rate=Decimal("18.00"),
        )
        self.prod1 = Product.objects.create(
            category=self.cat,
            sku="EC-CART-PROD-1",
            slug="ec-cart-prod-1",
            raw_name="Earphones 100",
            display_name="Earphones 100",
            source_asin="B00CART001",
            selling_price=Decimal("299.00"),
            mrp=Decimal("499.00"),
            is_available=True,
        )
        Inventory.objects.create(product=self.prod1, quantity=5)

        self.prod2 = Product.objects.create(
            category=self.cat,
            sku="EC-CART-PROD-2",
            slug="ec-cart-prod-2",
            raw_name="Headphones 500",
            display_name="Headphones 500",
            source_asin="B00CART002",
            selling_price=Decimal("1999.00"),
            mrp=Decimal("2999.00"),
            is_available=True,
        )
        Inventory.objects.create(product=self.prod2, quantity=10)

        self.user = User.objects.create_user(email="cartuser@example.com", password="SecurePassword123!")
        self.cart = get_or_create_cart(user=self.user)

    def test_add_to_cart_success(self):
        item = add_to_cart(self.cart, self.prod1, quantity=2)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(self.cart.items.count(), 1)
        self.assertEqual(item.line_subtotal, Decimal("598.00"))

    def test_add_to_cart_increments_existing_item(self):
        add_to_cart(self.cart, self.prod1, quantity=2)
        item = add_to_cart(self.cart, self.prod1, quantity=1)
        self.assertEqual(item.quantity, 3)

    def test_add_to_cart_clamps_to_available_stock(self):
        # prod1 has 5 in stock; adding 10 should clamp to 5
        item = add_to_cart(self.cart, self.prod1, quantity=10)
        self.assertEqual(item.quantity, 5)

    def test_add_out_of_stock_raises(self):
        oos_prod = Product.objects.create(
            category=self.cat,
            sku="EC-OOS-1",
            slug="ec-oos-1",
            raw_name="OOS Item",
            display_name="OOS Item",
            source_asin="B00OOS0001",
            selling_price=Decimal("199.00"),
            is_available=True,
        )
        Inventory.objects.create(product=oos_prod, quantity=0)

        with self.assertRaises(InsufficientStockError):
            add_to_cart(self.cart, oos_prod, quantity=1)

    def test_update_quantity(self):
        add_to_cart(self.cart, self.prod1, quantity=2)
        updated = update_cart_quantity(self.cart, self.prod1.id, quantity=4)
        self.assertEqual(updated.quantity, 4)

        # Update to 0 deletes
        rem = update_cart_quantity(self.cart, self.prod1.id, quantity=0)
        self.assertIsNone(rem)
        self.assertEqual(self.cart.items.count(), 0)

    def test_cart_calculator_under_and_over_free_shipping(self):
        # 1 item @ 299: subtotal 299 < 499 threshold -> standard fee 40.00
        add_to_cart(self.cart, self.prod1, quantity=1)
        summary = calculate_cart_summary(self.cart, buyer_state="KA", payment_method="razorpay")
        self.assertEqual(summary["subtotal"], Decimal("299.00"))
        self.assertEqual(summary["shipping_fee"], Decimal("40.00"))
        self.assertEqual(summary["mrp_savings"], Decimal("200.00"))
        self.assertEqual(summary["grand_total"], Decimal("339.00"))
        self.assertFalse(summary["is_free_shipping"])

        # Add prod2 @ 1999: subtotal 2298 >= 499 threshold -> shipping fee 0.00
        add_to_cart(self.cart, self.prod2, quantity=1)
        summary2 = calculate_cart_summary(self.cart, buyer_state="KA", payment_method="razorpay")
        self.assertEqual(summary2["subtotal"], Decimal("2298.00"))
        self.assertEqual(summary2["shipping_fee"], Decimal("0.00"))
        self.assertTrue(summary2["is_free_shipping"])
        self.assertEqual(summary2["free_shipping_progress_pct"], 100.0)

    def test_cart_calculator_cod_fee(self):
        cfg = ShippingConfig.get_solo()
        cfg.cod_fee = Decimal("50.00")
        cfg.save()

        add_to_cart(self.cart, self.prod1, quantity=1)
        summary = calculate_cart_summary(self.cart, buyer_state="MH", payment_method="cod")
        self.assertEqual(summary["cod_fee"], Decimal("50.00"))
        # subtotal 299 + shipping 40 + cod 50 = 389.00
        self.assertEqual(summary["grand_total"], Decimal("389.00"))

    def test_wishlist_toggle_and_move_to_cart(self):
        wishlist = get_or_create_wishlist(user=self.user)
        # Toggle on
        added = toggle_wishlist(wishlist, self.prod1)
        self.assertTrue(added)
        self.assertEqual(wishlist.items.count(), 1)

        # Move to cart
        cart_item = move_to_cart(wishlist, self.cart, self.prod1, quantity=1)
        self.assertEqual(cart_item.product, self.prod1)
        self.assertEqual(wishlist.items.count(), 0)
        self.assertEqual(self.cart.items.count(), 1)

    def test_merge_guest_cart_and_wishlist_on_login(self):
        guest_cart = get_or_create_cart(guest_token="guest_token_123")
        add_to_cart(guest_cart, self.prod1, quantity=1)

        user_cart = get_or_create_cart(user=self.user)
        add_to_cart(user_cart, self.prod2, quantity=1)

        merged_cart = merge_carts(guest_cart, user_cart)
        self.assertEqual(merged_cart.items.count(), 2)
        guest_cart.refresh_from_db()
        self.assertFalse(guest_cart.is_active)

        # Wishlist merge
        guest_wishlist = get_or_create_wishlist(guest_token="guest_token_123")
        toggle_wishlist(guest_wishlist, self.prod1)

        user_wishlist = get_or_create_wishlist(user=self.user)
        merged_wishlist = merge_wishlists(guest_wishlist, user_wishlist)
        self.assertEqual(merged_wishlist.items.count(), 1)
        guest_wishlist.refresh_from_db()
        self.assertEqual(guest_wishlist.items.count(), 0)
