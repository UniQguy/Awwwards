# ELECTROCART STOREFRONT ROUTE & URL REGISTRY

Comprehensive map of routes, views, templates, authorization rules, and context dictionaries.

| Route Pattern | URL Name | View Function | Template | Auth Rule | Context Keys |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/` | `home` | `apps.catalog.views.home` | `catalog/home.html` | Public | `total_products_count`, `categories_count`, `featured_collections`, `categories` |
| `/health/` | `health_check` | `apps.core.views.health_check` | (JSON) | Public | `status`, `service` |
| `/categories/` | `category_list` | `apps.catalog.views.category_list` | `catalog/category_list.html` | Public | `categories` |
| `/c/<slug:slug>/` | `category_detail` | `apps.catalog.views.category_detail` | `catalog/category_detail.html` | Public | `category`, `page_obj`, `facets`, `selected_filters`, `sort_by`, `collapsed`, `price_bars` |
| `/p/<slug:slug>/` | `product_detail` | `apps.catalog.views.product_detail` | `catalog/product_detail.html` | Public | `product`, `specifications`, `media_items`, `option_count`, `other_variants`, `related_products`, `delivery_estimate`, `remembered_pincode`, `max_cart_qty` |
| `/brands/` | `brand_list` | `apps.catalog.views.brand_list` | `catalog/brand_list.html` | Public | `brands_grouped` |
| `/compare/` | `compare_tray` | `apps.catalog.views.compare_tray` | `catalog/compare.html` | Public | `compared_products`, `spec_matrix`, `common_category` |
| `/compare/add/<int:product_id>/` | `compare_add` | `apps.catalog.views.compare_add` | (Redirect) | Public (POST) | Flash message |
| `/compare/remove/<int:product_id>/` | `compare_remove` | `apps.catalog.views.compare_remove` | (Redirect) | Public (POST) | Flash message |
| `/compare/clear/` | `compare_clear` | `apps.catalog.views.compare_clear` | (Redirect) | Public (POST) | Flash message |
| `/search/` | `search_results` | `apps.search.views.search_view` | `search/search_results.html` | Public | `query`, `products`, `page_obj`, `total_count`, `facets`, `did_you_mean`, `sort_by` |
| `/search/suggest/` | `search_suggest` | `apps.search.views.search_suggest` | (JSON) | Public | `suggestions` (products, categories, brands) |
| `/cart/` | `cart_detail` | `apps.cart.views.cart_detail` | `cart/cart_detail.html` | Public | `cart`, `summary`, `applied_coupon_code` |
| `/cart/add/<int:product_id>/` | `cart_add` | `apps.cart.views.cart_add` | (Redirect/JSON) | Public (POST) | Flash message / JSON |
| `/cart/update/<int:product_id>/` | `cart_update` | `apps.cart.views.cart_update` | (Redirect/JSON) | Public (POST) | Flash message / JSON |
| `/cart/remove/<int:product_id>/` | `cart_remove` | `apps.cart.views.cart_remove` | (Redirect/JSON) | Public (POST) | Flash message / JSON |
| `/cart/clear/` | `cart_clear` | `apps.cart.views.cart_clear` | (Redirect) | Public (POST) | Flash message |
| `/cart/coupon/apply/` | `coupon_apply` | `apps.cart.views.coupon_apply` | (Redirect) | Public (POST, Rate-limited) | Flash message |
| `/cart/coupon/remove/` | `coupon_remove` | `apps.cart.views.coupon_remove` | (Redirect) | Public (POST) | Flash message |
| `/wishlist/` | `wishlist_detail` | `apps.wishlist.views.wishlist_detail` | `wishlist/wishlist_detail.html` | Public | `wishlist`, `items` |
| `/wishlist/toggle/<int:product_id>/` | `wishlist_toggle` | `apps.wishlist.views.wishlist_toggle` | (Redirect/JSON) | Public (POST) | Flash message / JSON |
| `/wishlist/move-to-cart/<int:product_id>/` | `wishlist_move_to_cart` | `apps.wishlist.views.wishlist_move_to_cart` | (Redirect) | Public (POST) | Flash message |
| `/wishlist/remove/<int:product_id>/` | `wishlist_remove` | `apps.wishlist.views.wishlist_remove` | (Redirect) | Public (POST) | Flash message |
| `/shipping/check/` | `shipping_check` | `apps.shipping.views.shipping_check` | (Redirect/JSON) | Public (GET/POST, Rate-limited) | `estimate` / JSON |
| `/checkout/` | `checkout_start` | `apps.orders.views.checkout_start` | `orders/checkout_start.html` | Public | `cart`, `summary` |
| `/checkout/guest/` | `checkout_guest` | `apps.orders.views.checkout_guest` | (Redirect) | Public (POST) | Session step data |
| `/checkout/address/` | `checkout_address` | `apps.orders.views.checkout_address` | `orders/checkout_address.html` | Public (Cart required) | `saved_addresses`, `states`, `form_data` |
| `/checkout/review/` | `checkout_review` | `apps.orders.views.checkout_review` | `orders/checkout_review.html` | Public (Step verified) | `cart`, `summary`, `address`, `hold_expires_at`, `can_cod`, `can_razorpay` |
| `/checkout/place/` | `checkout_place` | `apps.orders.views.checkout_place` | (Redirect) | Public (POST, Rate-limited) | Flash message / redirect |
| `/payments/razorpay/checkout/<order_number>/` | `razorpay_checkout` | `apps.payments.views.razorpay_checkout_page` | `payments/razorpay_checkout.html` | Token / Owner | `order`, `key_id`, `amount_paise`, `token`, `can_cod` |
| `/payments/razorpay/verify/` | `razorpay_verify` | `apps.payments.views.razorpay_verify_view` | (JSON/Redirect) | Public (POST) | Verification status |
| `/payments/razorpay/webhook/` | `razorpay_webhook` | `apps.payments.views.razorpay_webhook_view` | (JSON) | Public (POST, CSRF-exempt) | Processing status |
| `/payments/failed/<order_number>/` | `payment_failed` | `apps.payments.views.payment_failed` | `payments/failed.html` | Token / Owner | `order`, `can_cod` |
| `/payments/cancelled/<order_number>/` | `payment_cancelled` | `apps.payments.views.payment_cancelled` | `payments/cancelled.html` | Token / Owner | `order` |
| `/payments/pending/<order_number>/` | `payment_pending` | `apps.payments.views.payment_pending` | `payments/pending.html` | Token / Owner | `order` |
| `/orders/<order_number>/success/` | `order_success` | `apps.orders.views.order_success` | `orders/order_success.html` | Token / Owner | `order`, `is_cod`, `token` |
| `/orders/<order_number>/cancel/` | `order_cancel` | `apps.orders.views.order_cancel` | (Redirect) | Token / Owner (POST) | Flash message |
| `/orders/<order_number>/invoice/` | `order_invoice` | `apps.orders.views.order_invoice` | `orders/invoice.html` | Token / Owner | `order`, `invoice`, `total_in_words`, `credit_notes` |
| `/orders/track/` | `order_track_lookup` | `apps.orders.views.order_track_lookup` | `orders/track_lookup.html` | Public (POST Rate-limited) | `form_data`, error |
| `/orders/track/<order_number>/verify/` | `order_track_timeline` | `apps.orders.views.order_track_timeline` | `orders/track_timeline.html` | Short-lived Session Grant | `order`, `tracking_info`, `status_history` |
| `/account/` | `account_dashboard` | `apps.accounts.views.account_dashboard` | `account/dashboard.html` | Login Required | `user`, `recent_orders`, `default_address` |
| `/account/orders/` | `account_order_list` | `apps.accounts.views.account_order_list` | `account/order_list.html` | Login Required | `orders`, `page_obj` |
| `/account/orders/<order_number>/` | `account_order_detail` | `apps.accounts.views.account_order_detail` | `account/order_detail.html` | Login Required (Owner) | `order`, `invoice` |
| `/account/addresses/` | `account_address_list` | `apps.accounts.views.account_address_list` | `account/address_list.html` | Login Required | `addresses` |
| `/account/addresses/create/` | `account_address_create` | `apps.accounts.views.account_address_form` | `account/address_form.html` | Login Required (GET/POST) | `states`, `errors` |
| `/account/addresses/<uuid:uuid>/edit/` | `account_address_edit` | `apps.accounts.views.account_address_form` | `account/address_form.html` | Login Required (Owner) | `address`, `states`, `errors` |
| `/account/addresses/<uuid:uuid>/delete/` | `account_address_delete` | `apps.accounts.views.account_address_delete` | (Redirect) | Login Required (POST) | Flash message |
| `/account/addresses/<uuid:uuid>/default/` | `account_address_set_default` | `apps.accounts.views.account_address_set_default` | (Redirect) | Login Required (POST) | Flash message |
| `/account/profile/` | `account_profile` | `apps.accounts.views.account_profile` | `account/profile.html` | Login Required (GET/POST) | `user`, `errors` |
| `/legal/terms/` | `legal_terms` | `apps.core.views.legal_terms` | `pages/terms.html` | Public | None |
| `/legal/privacy/` | `legal_privacy` | `apps.core.views.legal_privacy` | `pages/privacy.html` | Public | None |
| `/legal/shipping/` | `legal_shipping` | `apps.core.views.legal_shipping` | `pages/shipping.html` | Public | None |
| `/legal/refunds/` | `legal_refunds` | `apps.core.views.legal_refunds` | `pages/refunds.html` | Public | None |
