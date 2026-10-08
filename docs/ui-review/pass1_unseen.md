# Unseen Pages Review Register (Pass 1 - F-25)

Reviewed via Playwright Chromium at Desktop (1456px) and Mobile (390px).

| Page | Route | Desktop Status | Mobile Status | Desktop Screenshot | Mobile Screenshot |
|---|---|---|---|---|---|
| About | `/about/` | 200 | 200 | [desktop_about.png](desktop_about.png) | [mobile_about.png](mobile_about.png) |
| Terms | `/legal/terms/` | 200 | 200 | [desktop_terms.png](desktop_terms.png) | [mobile_terms.png](mobile_terms.png) |
| Refunds | `/legal/refunds/` | 200 | 200 | [desktop_refunds.png](desktop_refunds.png) | [mobile_refunds.png](mobile_refunds.png) |
| Shipping | `/legal/shipping/` | 200 | 200 | [desktop_shipping.png](desktop_shipping.png) | [mobile_shipping.png](mobile_shipping.png) |
| Privacy | `/legal/privacy/` | 200 | 200 | [desktop_privacy.png](desktop_privacy.png) | [mobile_privacy.png](mobile_privacy.png) |
| Categories | `/categories/` | 200 | 200 | [desktop_categories.png](desktop_categories.png) | [mobile_categories.png](mobile_categories.png) |
| Brands | `/brands/` | 200 | 200 | [desktop_brands.png](desktop_brands.png) | [mobile_brands.png](mobile_brands.png) |
| Empty Cart | `/cart/` | 200 | 200 | [desktop_empty_cart.png](desktop_empty_cart.png) | [mobile_empty_cart.png](mobile_empty_cart.png) |
| Login | `/accounts/login/` | 200 | 200 | [desktop_login.png](desktop_login.png) | [mobile_login.png](mobile_login.png) |
| Signup | `/accounts/signup/` | 200 | 200 | [desktop_signup.png](desktop_signup.png) | [mobile_signup.png](mobile_signup.png) |
| Page 404 | `/404-test-page/` | 404 | 404 | [desktop_page_404.png](desktop_page_404.png) | [mobile_page_404.png](mobile_page_404.png) |
| Page 403 | `/403-test/` | 403 | 403 | [desktop_page_403.png](desktop_page_403.png) | [mobile_page_403.png](mobile_page_403.png) |
| Page 403 Csrf | `/403-csrf-test/` | 403 | 403 | [desktop_page_403_csrf.png](desktop_page_403_csrf.png) | [mobile_page_403_csrf.png](mobile_page_403_csrf.png) |
| Page 429 | `/429-test/` | 429 | 429 | [desktop_page_429.png](desktop_page_429.png) | [mobile_page_429.png](mobile_page_429.png) |
| Page 500 | `/500-test/` | 500 | 500 | [desktop_page_500.png](desktop_page_500.png) | [mobile_page_500.png](mobile_page_500.png) |


## Observations & Design Language Conformity
- **Warm Paper Background**: All utility and legal pages inherit `--color-warm-paper` / `--world-surface`.
- **Calm Copy**: Error templates (403, 404, 429, 500) use direct, unadorned explanations without techno-babble.
- **Table Responsiveness**: Tables and forms on mobile (390px) collapse cleanly without horizontal viewport overflow.
- **Honesty Rules**: No promotional banners or unverified claims present on legal or error views.
