"""
Tests for ReportLab PDF statutory GST invoice and credit note generation.
Verifies:
- Layout and content accuracy (Order number, Seller GSTIN, Buyer, Items, HSN, Totals)
- UTF-8 and Rupee symbol (₹, U+20B9) font rendering without UnicodeEncodeError
- Indian words currency representation
- Sample data honesty notice
- Credit Note generation and invoice cross-referencing
- HTTP view access control
- Execution performance (10 invoices under 2.5 seconds)
- Up to 10 items fitting on a single A4 page
"""

from decimal import Decimal
import io
import time
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
import pypdf

from apps.catalog.models import Category, Product
from apps.orders.models import CreditNote, Invoice, Order, OrderItem
from apps.orders.services.invoice_pdf import build_credit_note_pdf, build_invoice_pdf
from apps.orders.services.invoicing import generate_credit_note, generate_invoice
from apps.orders.utils.number_words import number_to_words_inr

User = get_user_model()


class PDFInvoiceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="arun.kumar@example.com",
            full_name="Arun Kumar",
            password="SecurePassword123!",
        )

        self.category = Category.objects.create(name="Audio Equipment", slug="audio-equipment")

        self.product1 = Product.objects.create(
            raw_name="Sony WH-1000XM5 Wireless Headphones",
            display_name="Sony WH-1000XM5 Wireless Headphones",
            slug="sony-wh-1000xm5",
            sku="SNY-WH1000XM5-BLK",
            source_asin="B09XS7JWHH",
            category=self.category,
            parsed_brand="Sony",
            selling_price=Decimal("24990.00"),
            mrp=Decimal("29990.00"),
            is_available=True,
        )

        self.product2 = Product.objects.create(
            raw_name="Premium 3.5mm Braided Audio Cable",
            display_name="Premium 3.5mm Braided Audio Cable",
            slug="braided-audio-cable",
            sku="CBL-AUX-35MM",
            source_asin="B09CBLAUX1",
            category=self.category,
            parsed_brand="Electrocart Essentials",
            selling_price=Decimal("999.00"),
            mrp=Decimal("1499.00"),
            is_available=True,
        )

        self.order = Order.objects.create(
            order_number="EC-20261007-8801",
            user=self.user,
            shipping_address_snapshot={
                "full_name": "Arun Kumar",
                "phone": "9876543210",
                "line1": "Flat 402, Shanti Nilayam",
                "line2": "12th Main, Indiranagar",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560038",
            },
            status=Order.STATUS_CONFIRMED,
            payment_method=Order.PAYMENT_METHOD_COD,
            payment_status=Order.PAYMENT_STATUS_PENDING,
            subtotal=Decimal("25989.00"),
            shipping_fee=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("3964.42"),
            total_amount=Decimal("25989.00"),
            is_sample_data=False,
        )

        OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            product_title="Sony WH-1000XM5 Wireless Headphones",
            product_sku="SNY-WH1000XM5-BLK",
            unit_price=Decimal("24990.00"),
            mrp=Decimal("29990.00"),
            quantity=1,
            hsn_code="8518",
            gst_rate=Decimal("18.00"),
            taxable_value=Decimal("21177.97"),
            cgst_amount=Decimal("1906.02"),
            sgst_amount=Decimal("1906.01"),
            line_total=Decimal("24990.00"),
        )

        OrderItem.objects.create(
            order=self.order,
            product=self.product2,
            product_title="Premium 3.5mm Braided Audio Cable",
            product_sku="CBL-AUX-35MM",
            unit_price=Decimal("999.00"),
            mrp=Decimal("1499.00"),
            quantity=1,
            hsn_code="8544",
            gst_rate=Decimal("18.00"),
            taxable_value=Decimal("846.61"),
            cgst_amount=Decimal("76.19"),
            sgst_amount=Decimal("76.20"),
            line_total=Decimal("999.00"),
        )

        self.invoice = generate_invoice(self.order)

    def test_invoice_pdf_content_and_encoding(self):
        """
        Verify that generated invoice PDF contains all required metadata,
        statutory declarations, HSN codes, totals in figures and words,
        and renders ₹ without UnicodeEncodeError.
        """
        pdf_bytes = build_invoice_pdf(self.order, invoice=self.invoice)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        self.assertGreaterEqual(len(reader.pages), 1)

        extracted_text = ""
        for page in reader.pages:
            extracted_text += page.extract_text() + "\n"

        # Assert key business & statutory content
        self.assertIn("ELECTROCART", extracted_text)
        self.assertIn(self.order.order_number, extracted_text)
        self.assertIn(self.invoice.invoice_number, extracted_text)
        self.assertIn("Arun Kumar", extracted_text)
        self.assertIn("Bengaluru", extracted_text)
        self.assertIn("Karnataka", extracted_text)
        self.assertIn("Sony WH-1000XM5", extracted_text)
        self.assertIn("8518", extracted_text)
        self.assertIn("8544", extracted_text)

        # Assert total in figures and words
        self.assertIn("25989.00", extracted_text)
        self.assertIn("Rupees", extracted_text)
        self.assertIn("Twenty Five Thousand Nine Hundred Eighty Nine Only", extracted_text)

        # Assert Rupee currency symbol rendered correctly
        self.assertIn("₹", extracted_text)

        # Assert statutory legal declaration
        self.assertIn("computer generated invoice", extracted_text)
        normalized_text = " ".join(extracted_text.split())
        self.assertIn("Subject to Delhi jurisdiction", normalized_text)

        # Sample data notice must NOT be present when is_sample_data=False
        self.assertNotIn("SAMPLE DATA NOTICE", extracted_text)

    def test_sample_data_honesty_label(self):
        """Verify that when is_sample_data=True, the invoice clearly includes the sample notice."""
        self.order.is_sample_data = True
        self.order.save()

        pdf_bytes = build_invoice_pdf(self.order, invoice=self.invoice)
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = "".join(page.extract_text() for page in reader.pages)

        self.assertIn("SAMPLE DATA NOTICE", text)
        self.assertIn("demonstration / sample mode", text)

    def test_credit_note_pdf_generation(self):
        """Verify that a cancelled order generates a formal GST Credit Note referencing original invoice."""
        self.order.status = Order.STATUS_CANCELLED
        self.order.save()

        cn = generate_credit_note(self.order, reason="Customer cancelled before dispatch.")
        pdf_bytes = build_credit_note_pdf(self.order, credit_note=cn)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = "".join(page.extract_text() for page in reader.pages)

        self.assertIn("CREDIT NOTE", text)
        self.assertIn(cn.credit_note_number, text)
        self.assertIn(self.invoice.invoice_number, text)
        self.assertIn("Customer cancelled before dispatch", text)
        self.assertIn("Rupees", text)
        self.assertIn("₹", text)

    def test_invoice_pdf_view_authorized_and_unauthorized(self):
        """Verify access control on /orders/<order_number>/invoice/pdf/."""
        url = f"/orders/{self.order.order_number}/invoice/pdf/"

        # Unauthenticated request without token -> 404
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        # Authenticated as the order customer -> 200 with PDF content type
        self.client.force_login(self.user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["Content-Type"], "application/pdf")
        self.assertIn(f"{self.invoice.invoice_number}.pdf", resp.headers["Content-Disposition"])

    def test_credit_note_pdf_view(self):
        """Verify access control on /orders/<order_number>/credit-note/pdf/."""
        self.order.status = Order.STATUS_CANCELLED
        self.order.save()
        generate_credit_note(self.order, reason="Cancelled")

        url = f"/orders/{self.order.order_number}/credit-note/pdf/"
        self.client.force_login(self.user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["Content-Type"], "application/pdf")

    def test_ten_items_fit_on_single_page(self):
        """
        Verify that an invoice with up to 10 line items comfortably fits on a single A4 page.
        """
        multi_order = Order.objects.create(
            order_number="EC-20261007-10IT",
            user=self.user,
            shipping_address_snapshot=self.order.shipping_address_snapshot,
            status=Order.STATUS_CONFIRMED,
            payment_method=Order.PAYMENT_METHOD_COD,
            subtotal=Decimal("10000.00"),
            total_amount=Decimal("11800.00"),
            tax_amount=Decimal("1800.00"),
        )
        for i in range(1, 11):
            OrderItem.objects.create(
                order=multi_order,
                product=self.product1,
                product_title=f"Sample Electronic Accessory #{i}",
                product_sku=f"SKU-{i:03d}",
                unit_price=Decimal("1000.00"),
                mrp=Decimal("1200.00"),
                quantity=1,
                hsn_code="8518",
                gst_rate=Decimal("18.00"),
                taxable_value=Decimal("847.46"),
                cgst_amount=Decimal("76.27"),
                sgst_amount=Decimal("76.27"),
                line_total=Decimal("1000.00"),
            )
        inv = generate_invoice(multi_order)
        pdf_bytes = build_invoice_pdf(multi_order, invoice=inv)
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        self.assertEqual(len(reader.pages), 1, "An invoice with 10 items must fit on 1 A4 page")

    def test_performance_ten_invoices_under_2_point_5_seconds(self):
        """
        Generate 10 invoices in a loop and assert total wall-clock time is under 2.5s.
        """
        start = time.perf_counter()
        for _ in range(10):
            pdf = build_invoice_pdf(self.order, invoice=self.invoice)
            self.assertGreater(len(pdf), 500)
        elapsed = time.perf_counter() - start

        self.assertLess(
            elapsed,
            2.5,
            f"10 PDF invoices took {elapsed:.2f}s, exceeding 2.5s target",
        )
