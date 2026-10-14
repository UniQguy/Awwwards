# BUSINESS FLOW & SECURITY LOOPHOLE REVIEW (ELECTROCART)

This document provides a comprehensive audit of high-risk commercial e-commerce loopholes, how ELECTROCART's architecture structurally prevents each vulnerability, the exact lines of code enforcing the guardrails, and the automated tests verifying them.

---

## 1. Price Tampering (Server-Truth Pricing)

- **Vulnerability**: A malicious client alters product prices, discounts, or subtotals in HTTP POST payloads (e.g. submitting `amount=1.00`).
- **Architectural Prevention**: The storefront never reads or trusts client-supplied monetary values. When `place_order` is invoked, the order subtotal, item prices, and statutory GST amounts are strictly computed from authoritative database records (`Product.selling_price`) and current catalog tax configurations.
- **Enforcing Code**:
  - [`apps/orders/services/order_creator.py#L62-L68`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/orders/services/order_creator.py#L62-L68):
    ```python
    summary = calculate_cart_summary(
        cart=cart,
        buyer_state=buyer_state,
        coupon_discount=applied_discount,
        payment_method=payment_method,
    )
    ```
- **Automated Verification**:
  - [`tests/test_flow_review.py::BusinessFlowAndSecurityTests.test_price_tampering_rejected_server_truth`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/tests/test_flow_review.py): Validates that an injected price is ignored, producing the exact database-backed amount of ₹4,999.00.

---

## 2. Stock Oversell & Concurrency Race Conditions

- **Vulnerability**: Two buyers simultaneously attempt to purchase the final remaining unit of physical stock, leading to negative inventory or unfulfillable orders.
- **Architectural Prevention**:
  1. Unreserved stock is calculated as on-hand inventory minus all active, unexpired reservations (`get_available_stock`).
  2. New stock reservations check available capacity before creation.
  3. Conversion from reservation to permanent sale executes an atomic conditional update (`UPDATE inventory SET quantity = quantity - N WHERE quantity >= N`). If physical quantity is insufficient, `rows_updated == 0` raises `InsufficientStockError`, rolling back the atomic transaction.
- **Enforcing Code**:
  - [`apps/inventory/services/reservation_service.py#L22-L44`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/inventory/services/reservation_service.py#L22-L44): Real-time stock calculation querying database inventory.
  - [`apps/inventory/services/reservation_service.py#L144-L155`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/inventory/services/reservation_service.py#L144-L155):
    ```python
    rows_updated = Inventory.objects.filter(
        product=res.product,
        quantity__gte=res.quantity,
    ).update(quantity=F("quantity") - res.quantity)
    if rows_updated == 0:
        raise InsufficientStockError(res.product.sku, res.quantity, 0)
    ```
- **Automated Verification**:
  - [`tests/test_flow_review.py::BusinessFlowAndSecurityTests.test_stock_oversell_race_condition`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/tests/test_flow_review.py): Verifies that when 1 physical unit exists, buyer 1 successfully reserves/converts, while buyer 2 receives `InsufficientStockError`.

---

## 3. Coupon Limits & Zero Stacking

- **Vulnerability**: Buyers bypass usage caps by repeatedly redeeming single-use coupons, or stack multiple discount codes to achieve 100% discount.
- **Architectural Prevention**:
  1. `validate_coupon` checks `usage_limit_total` against `coupon.redemptions.count()` (`GLOBAL_LIMIT_EXCEEDED`).
  2. `validate_coupon` checks `usage_limit_per_user` against `coupon.redemptions.filter(user=user).count()` (`USER_LIMIT_EXCEEDED`).
  3. The cart session stores a single string key `request.session["applied_coupon_code"]`. Applying any coupon overwrites the existing coupon; coupon stacking is impossible.
- **Enforcing Code**:
  - [`apps/promotions/services/coupon_validator.py#L92-L113`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/promotions/services/coupon_validator.py#L92-L113):
    ```python
    if coupon.usage_limit_total is not None and coupon.redemptions.count() >= coupon.usage_limit_total:
        return CouponValidationResult(is_valid=False, reason_code=REASON_GLOBAL_LIMIT)
    if user and user.is_authenticated and coupon.usage_limit_per_user:
        if coupon.redemptions.filter(user=user).count() >= coupon.usage_limit_per_user:
            return CouponValidationResult(is_valid=False, reason_code=REASON_USER_LIMIT)
    ```
  - [`apps/cart/views.py#L293`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/cart/views.py#L293): `request.session["applied_coupon_code"] = result.coupon.code`
- **Automated Verification**:
  - [`tests/test_flow_review.py::BusinessFlowAndSecurityTests.test_coupon_usage_limits_and_no_stacking`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/tests/test_flow_review.py): Proves per-user limit rejection, global limit rejection, and single-coupon replacement in the session.

---

## 4. Duplicate Place Order (Double-Click / Idempotency)

- **Vulnerability**: Rapid double-clicking on the "Place Order" button or network replay creates duplicate orders and double-bills the customer.
- **Architectural Prevention**:
  - `checkout_place` checks `if not cart.items.exists(): return redirect("cart_detail")`.
  - Inside `place_order`, an atomic database transaction generates the order, reserves stock, and invokes `clear_cart(cart)`.
  - The second incoming request finds zero items in the cart and immediately aborts with an informational redirect, preventing duplicate orders.
- **Enforcing Code**:
  - [`apps/orders/views.py#L307-L310`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/orders/views.py#L307-L310):
    ```python
    cart = _get_cart(request)
    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart_detail")
    ```
  - [`apps/orders/services/order_creator.py#L155`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/orders/services/order_creator.py#L155): `clear_cart(cart)` executed inside `with transaction.atomic():`.
- **Automated Verification**:
  - [`tests/test_flow_review.py::BusinessFlowAndSecurityTests.test_duplicate_place_order_idempotent`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/tests/test_flow_review.py): Submits `checkout_place` twice sequentially; asserts second submission creates 0 new orders and redirects gracefully.

---

## 5. Session Expiry Mid-Checkout

- **Vulnerability**: A customer leaves the checkout page open, the session cookie expires, and submitting the form creates an orphan or unaddressable order.
- **Architectural Prevention**:
  - `checkout_place` verifies `address = request.session.get("checkout_address")`.
  - If the session expired or address data is absent, the view cleanly redirects back to `checkout_address` (or `checkout_start`) with a user-facing flash message. No order is created.
- **Enforcing Code**:
  - [`apps/orders/views.py#L312-L315`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/orders/views.py#L312-L315):
    ```python
    address = request.session.get("checkout_address")
    if not address:
        messages.error(request, "Delivery address missing.")
        return redirect("checkout_address")
    ```
- **Automated Verification**:
  - [`tests/test_flow_review.py::BusinessFlowAndSecurityTests.test_session_expiry_mid_checkout`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/tests/test_flow_review.py): Validates redirection to `/checkout/address/` when `checkout_address` key is missing from session.

---

## 6. Guest Order Enumeration / IDOR

- **Vulnerability**: An attacker changes the order ID parameter to scrape order history, customer names, phone numbers, and addresses.
- **Architectural Prevention**:
  1. Order numbers use high-entropy random identifiers (`EC-YYYY-XXXX-XXXX`), preventing sequential ID guessing.
  2. Public access to order details and invoices is gated by `_validate_order_access`:
     - If authenticated, the customer must match `order.user`.
     - If a guest, the request must supply a cryptographic UUID token matching the session-established token, or pass phone/email verification on `/orders/track/`.
     - Unauthorized access returns HTTP 404 (revealing neither order existence nor customer data).
- **Enforcing Code**:
  - [`apps/orders/views.py#L47-L65`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/orders/views.py#L47-L65):
    ```python
    def _validate_order_access(request: HttpRequest, order: Order) -> bool:
        if request.user.is_authenticated and order.user == request.user:
            return True
        token = request.GET.get("token") or request.session.get(f"order_token_{order.order_number}")
        session_token = request.session.get(f"order_token_{order.order_number}")
        if token and token == session_token:
            return True
        if request.session.get(f"track_grant_{order.order_number}"):
            return True
        return False
    ```
- **Automated Verification**:
  - [`tests/test_flow_review.py::BusinessFlowAndSecurityTests.test_guest_order_enumeration_idor`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/tests/test_flow_review.py): Confirms HTTP 404 for unauthenticated visitors, foreign authenticated users, and invalid tokens.

---

## 7. CSRF Protection Across Mutating Endpoints

- **Vulnerability**: Cross-Site Request Forgery (CSRF) forcing unauthorized cart manipulation, coupon application, or checkout execution.
- **Architectural Prevention**: Django's `CsrfViewMiddleware` enforces CSRF tokens across all state-altering POST endpoints. All storefront forms render `{% csrf_token %}` and JavaScript fetch utilities forward the `X-CSRFToken` header.
- **Enforcing Code**:
  - `config/settings/base.py`: `django.middleware.csrf.CsrfViewMiddleware`.
  - Templates: `{% csrf_token %}` present on every `<form method="post">`.
- **Automated Verification**:
  - [`tests/test_flow_review.py::BusinessFlowAndSecurityTests.test_csrf_protection_on_all_post_endpoints`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/tests/test_flow_review.py): Asserts HTTP 403 on `/cart/add/`, `/cart/save-for-later/`, `/cart/move-to-bag/`, `/cart/remove/`, `/cart/coupon/apply/`, and `/checkout/place/` when CSRF checks are enforced.

---

## 8. Rate Limiting (HTTP 429)

- **Vulnerability**: Brute-force attacks enumerating coupon codes, checking serviceability PINs, spamming checkout submissions, or overwhelming search suggestions.
- **Architectural Prevention**: Endpoints are decorated with `django_ratelimit` by client IP:
  - `checkout_place`: 10 requests / minute
  - `coupon_apply`: 10 requests / minute
  - `shipping_check`: 20 requests / minute
  - `order_track_lookup`: 20 requests / minute
  - `search_suggest`: 60 requests / minute
- **Enforcing Code**:
  - [`apps/orders/views.py#L296`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/orders/views.py#L296): `@ratelimit(key="ip", rate="10/m", block=False)`
  - [`apps/cart/views.py#L272`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/cart/views.py#L272): `@ratelimit(key="ip", rate="10/m", block=False)`
  - [`apps/shipping/views.py#L15`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/shipping/views.py#L15): `@ratelimit(key="ip", rate="20/m", block=False)`
- **Automated Verification**:
  - [`tests/test_flow_review.py::BusinessFlowAndSecurityTests.test_rate_limits_enforced_429`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/tests/test_flow_review.py): Exceeds limits on `coupon_apply` and `shipping_check`, asserting HTTP 429 status code.

---

## 9. Webhook Signature Spoofing & Replay Protection

- **Vulnerability**: Attackers inject fake payment confirmation webhooks or replay captured payloads to artificially mark unpaid orders as confirmed.
- **Architectural Prevention**:
  1. Inbound Razorpay webhooks verify HMAC-SHA256 signatures against `RAZORPAY_WEBHOOK_SECRET` before parsing JSON. Invalid signatures immediately raise `PermissionError` returning HTTP 403.
  2. Events are recorded in `WebhookEvent` table using atomic `select_for_update().get_or_create(event_id=event_id)`.
  3. If an event ID has already been processed (`is_processed=True`), the endpoint safely returns `{"status": "already_processed"}` with HTTP 200 without re-executing inventory decrements or invoice generation.
- **Enforcing Code**:
  - [`apps/payments/views.py#L160-L183`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/payments/views.py#L160-L183):
    ```python
    @csrf_exempt
    @ratelimit(key="ip", rate="120/m", block=False)
    @require_POST
    def razorpay_webhook_view(request: HttpRequest) -> JsonResponse:
        ...
        res = process_webhook_payload(raw_body=raw_body, signature_header=signature)
    ```
  - [`apps/payments/services/webhook_processor.py#L111-L128`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/apps/payments/services/webhook_processor.py#L111-L128): Signature verification and atomic deduplication.
- **Automated Verification**:
  - [`tests/test_flow_review.py::BusinessFlowAndSecurityTests.test_webhook_replay_and_signature_spoofing`](file:///c:/Users/PRASHANT/Downloads/RootDirectory/tests/test_flow_review.py): Validates HTTP 403 on spoofed signature and `"status": "already_processed"` on replayed event delivery.
