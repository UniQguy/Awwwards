"""
Tests for apps.tax: extraction vectors, CGST/SGST split, line allocator, and supply resolution.
"""

from decimal import Decimal
import random
from django.test import SimpleTestCase

from apps.tax.exceptions import InvalidStateError, MissingSellerStateError
from apps.tax.services.gst_calculator import extract_tax, resolve_supply, split_tax
from apps.tax.services.line_allocator import allocate_order_lines
from apps.tax.states import normalize_state_name


class TaxEngineUnitTests(SimpleTestCase):
    """Unit tests for GST calculator formulas and state resolution."""

    def test_extraction_vector_1299_at_18_percent(self):
        """
        Verification vector: ₹1,299 at 18% GST.
        Exact fraction: 1299 * 18 / 118 = 198.152542...
        Rounded HALF_UP: tax = ₹198.15, taxable = ₹1,100.85.
        """
        price = Decimal("1299.00")
        rate = Decimal("18.00")
        tax = extract_tax(price, rate)
        taxable = price - tax

        self.assertEqual(tax, Decimal("198.15"))
        self.assertEqual(taxable, Decimal("1100.85"))
        self.assertEqual(tax + taxable, price)

    def test_odd_paise_cgst_sgst_split(self):
        """
        Odd paise tax (e.g. ₹198.15) must split cleanly with zero lost paise:
        CGST = ₹99.08, SGST = ₹99.07, Sum = ₹198.15.
        """
        tax = Decimal("198.15")
        cgst, sgst, igst = split_tax(tax, intra_state=True)

        self.assertEqual(cgst, Decimal("99.08"))
        self.assertEqual(sgst, Decimal("99.07"))
        self.assertEqual(igst, Decimal("0.00"))
        self.assertEqual(cgst + sgst, tax)

    def test_inter_state_split(self):
        tax = Decimal("198.15")
        cgst, sgst, igst = split_tax(tax, intra_state=False)

        self.assertEqual(cgst, Decimal("0.00"))
        self.assertEqual(sgst, Decimal("0.00"))
        self.assertEqual(igst, Decimal("198.15"))

    def test_bill_of_supply_extracts_zero_tax(self):
        price = Decimal("1299.00")
        rate = Decimal("18.00")
        tax = extract_tax(price, rate, registered=False)
        self.assertEqual(tax, Decimal("0.00"))

    def test_state_normalization_and_unknown_state_error(self):
        self.assertEqual(normalize_state_name("  karnataka "), "Karnataka")
        self.assertEqual(normalize_state_name("GUJARAT"), "Gujarat")
        self.assertEqual(normalize_state_name("Delhi"), "Delhi")

        with self.assertRaises(InvalidStateError):
            normalize_state_name("California")

        with self.assertRaises(InvalidStateError):
            normalize_state_name("")

    def test_resolve_supply(self):
        is_intra, delivery, seller = resolve_supply("Karnataka", "Karnataka")
        self.assertTrue(is_intra)
        self.assertEqual(delivery, "Karnataka")
        self.assertEqual(seller, "Karnataka")

        is_intra, delivery, seller = resolve_supply("Maharashtra", "Karnataka")
        self.assertFalse(is_intra)

    def test_missing_seller_state_raises_error(self):
        with self.assertRaises(MissingSellerStateError):
            resolve_supply("Karnataka", "")


class LineAllocatorTests(SimpleTestCase):
    """Tests for multi-line discount allocation and tax balance invariants."""

    def test_zero_discount_allocation(self):
        lines = [
            {"quantity": 1, "unit_price_incl": Decimal("1000.00"), "rate": Decimal("18.00")},
            {"quantity": 2, "unit_price_incl": Decimal("500.00"), "rate": Decimal("18.00")},
        ]
        result = allocate_order_lines(lines, discount_total=Decimal("0.00"), shipping_fee=Decimal("40.00"))

        self.assertEqual(result.items_subtotal, Decimal("2000.00"))
        self.assertEqual(result.discount_amount, Decimal("0.00"))
        self.assertEqual(result.grand_total, Decimal("2040.00"))
        self.assertEqual(result.total_taxable_value + result.total_tax_amount, result.grand_total)

    def test_discount_proportional_largest_remainder(self):
        # 3 items of 100, 200, 300 with 50 discount
        lines = [
            {"quantity": 1, "unit_price_incl": Decimal("100.00"), "rate": Decimal("18.00")},
            {"quantity": 1, "unit_price_incl": Decimal("200.00"), "rate": Decimal("18.00")},
            {"quantity": 1, "unit_price_incl": Decimal("300.00"), "rate": Decimal("18.00")},
        ]
        result = allocate_order_lines(lines, discount_total=Decimal("50.00"))

        # Check discounts sum to exactly 50.00
        discounts = [l.discount_share for l in result.lines]
        self.assertEqual(sum(discounts), Decimal("50.00"))
        self.assertEqual(result.total_taxable_value + result.total_tax_amount, result.grand_total)

    def test_full_discount_allocation(self):
        lines = [
            {"quantity": 1, "unit_price_incl": Decimal("500.00"), "rate": Decimal("18.00")},
        ]
        result = allocate_order_lines(lines, discount_total=Decimal("500.00"), shipping_fee=Decimal("40.00"))

        self.assertEqual(result.items_net_total, Decimal("0.00"))
        self.assertEqual(result.grand_total, Decimal("40.00"))
        self.assertEqual(result.total_taxable_value + result.total_tax_amount, result.grand_total)

    def test_bill_of_supply_mode(self):
        lines = [
            {"quantity": 2, "unit_price_incl": Decimal("500.00"), "rate": Decimal("18.00")},
        ]
        result = allocate_order_lines(lines, registered=False)

        self.assertEqual(result.total_tax_amount, Decimal("0.00"))
        self.assertEqual(result.total_taxable_value, Decimal("1000.00"))
        self.assertEqual(result.grand_total, Decimal("1000.00"))

    def test_property_invariant_random_baskets(self):
        """
        Fuzz test across 50 randomly generated baskets with varying rates,
        quantities, prices, discounts, and fees.
        INVARIANT: total_taxable_value + total_tax_amount == grand_total (always).
        INVARIANT: total_cgst + total_sgst + total_igst == total_tax_amount (always).
        """
        random.seed(42)
        rates = [Decimal("0.00"), Decimal("5.00"), Decimal("12.00"), Decimal("18.00"), Decimal("28.00")]

        for _ in range(50):
            num_lines = random.randint(1, 6)
            lines = []
            for _ in range(num_lines):
                qty = random.randint(1, 4)
                price = Decimal(str(random.randint(50, 10000))) + Decimal(str(random.choice([0, 0.25, 0.50, 0.99])))
                rate = random.choice(rates)
                lines.append({"quantity": qty, "unit_price_incl": price, "rate": rate})

            subtotal = sum(l["quantity"] * l["unit_price_incl"] for l in lines)
            discount = Decimal(str(random.randint(0, int(subtotal))))
            shipping = Decimal(str(random.choice([0, 40, 80])))
            cod = Decimal(str(random.choice([0, 50])))
            intra = random.choice([True, False])
            reg = random.choice([True, False])

            alloc = allocate_order_lines(lines, discount, shipping, cod, intra_state=intra, registered=reg)

            # Invariants
            self.assertEqual(
                alloc.total_taxable_value + alloc.total_tax_amount,
                alloc.grand_total,
                f"Taxable {alloc.total_taxable_value} + Tax {alloc.total_tax_amount} != Grand {alloc.grand_total}"
            )
            self.assertEqual(
                alloc.total_cgst + alloc.total_sgst + alloc.total_igst,
                alloc.total_tax_amount,
                f"Split components do not sum to total tax"
            )
