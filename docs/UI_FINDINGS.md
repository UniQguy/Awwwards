UI FINDINGS REGISTER (from owner screenshots taken after Phase 7, desktop viewport about 1456 px wide). Severity: S0 blocks use or breaks honesty; S1 clearly visible defect; S2 polish.

S0
F-01 Guest checkout is dead. Cart > "Proceed to Checkout" lands on /checkout/guest/ showing "403 Forbidden: You do not have permission to access this resource or your session validation failed." Cause not yet known; do not assume.
F-02 Wrong categories. Home Cameras chapter shows Redmi Note 10S phones (title mentions "Super Amoled Display", camera) and SanDisk SD cards. Displays and Televisions chapter shows a Fire TV Stick. Classifier lets device words and accessory words steal products.
F-03 Wrong specs. Screen size reads centimetres as inches: Redmi "80 cm (32 inches)" shows 80", "108 cm (43 inches)" shows 108", "126 cm (50 inches)" shows 126"; Noise watch 1.69" (4.29cm) shows 4.29". Specs parsed from titles must never be wrong.
F-04 Invented copy that contradicts the data: category descriptions ("Flagship smartphones...pocket communicators" above a Redmi 9A Sport; "OLED cinema panels, ultra-wide studio monitors"; "Mirrorless camera bodies, cinema prime lenses, gimbals"; "Architectural bookshelf speakers, Dolby Atmos soundbars"; "High-fidelity studio monitors, active noise-cancelling headphones"), "precision electronics and honest craft" (closing line), "precision electronics and audio equipment" (footer), "An architectural directory of specialized hardware worlds, calibrated materials, and acoustic instruments" (categories index), "within statutory limits", "Payment Authorization", "Explore hardware manufactured by" (brands; these are brands, not necessarily makers).
F-05 Tax mode contradiction. Footer says "Composition Dealer / Unregistered. Issuing Bill of Supply." and the home says prices are "net under Bill of Supply mode", yet the cart shows "Taxes (GST) Included (₹66.96)" and "Prices are inclusive of applicable GST under Indian tax regulations." In Bill of Supply mode no GST is charged or shown anywhere. Also "Composition Dealer" and "Unregistered" are different legal statuses and must not be asserted.
F-06 Cart arithmetic does not foot. Summary shows Items Subtotal ₹399, "Retail Savings (MRP) -₹600", Shipping ₹40, Grand Total ₹439. The savings line reads as a deduction but is not in the sum.

S1
F-07 Header search: typing "head" shows no suggestions panel. Verify in a real browser; the feature may be missing or failing.
F-08 Home hero: about 400 px of empty space above the headline at first load; the first screen shows no headline, only part of the plate. The auto-selected hero product is an HDMI cable.
F-09 Inline cutouts are tiny boxed squares with visible white backgrounds, not blended or skewed, and punctuation floats apart ("listening [img] , tools for thought [img] ,").
F-10 Home chapters: the fourth plate drops alone onto a second row leaving a large void; sections have no bottom padding so plates touch the next chapter's seam; plates have uneven widths, so narrow ones cramp.
F-11 Product cards: names set in bold Fraunces wrapping to 5 to 7 lines (spec: Plus Jakarta Sans 500, two-line clamp); titles cut mid-phrase ("Vibrant Colors with", "kids learning & added"); the "View ->" link wraps onto two lines in narrow cards; price and MRP collide ("₹1,200View->"); every card repeats the category name already shown by the chapter.
F-12 Chapter picks are near-duplicates: three boAt Bassheads 100 colours, three Redmi 9A Sport variants, two Fitbit Versa 2.
F-13 Plate image treatment: photos sit in a lighter square window on the darker plate instead of blending into it (multiply is not dissolving the white against the plate colour).
F-14 World colour does not reach the chrome: header rule stays terracotta over green and blue chapters; neighbouring chapters (clay then clay) look identical so the seams and worlds do not read.
F-15 Categories index: product images are enormous (about 800 px, upscaled, cropped, overflowing the viewport); heading "Category Monograph Index" is jargon.
F-16 "How purchasing works": three equal columns (the banned three-cards pattern in text form), about 200 px of dead space above and below, awkward copy.
F-17 Brands paragraph: dangling "·" separators at line ends and at the end, brand names break across lines ("Ant / Esports"), counts illegible, intro text fused with the first link.
F-18 Closing line is centred while the whole page is left-aligned; claims "precision" and "craft".
F-19 Login: "Forgot password" appears twice; "Remember Me" label sits above a centred checkbox; required asterisks float at the far right; placeholders duplicate labels; fields are stark white and square-cornered against the warm page; heading centred, rest left.
F-20 Wishlist: breadcrumb starts at x=129 while the heading starts at x=84 (inconsistent container); generic empty state; uses "Wishlist" while the UI voice is "bag".
F-21 Header: search icon looks like a loading spinner; heart is clipped; "Shop" chevron is a stray curve; the search field is a pill while the system is sharp-edged; accent rule under the header is heavy (2 px solid terracotta).
F-22 Footer: dev-speak "Crafted with semantic HTML & native web standards." with a stray " ."; "Reduce motion: Off" indented out of its column; no notice that prices and stock are old sample data (only "Demonstration catalog").
F-23 Error pages: 403 copy is machine-speak, not the brand voice; tiny lock icon.
F-24 Cart: promo field placeholder truncated and gives an example code; thumbnail small and cropped; half the page is empty under the line items.

S2
F-25 Pages not yet seen by the reviewer (must be inspected and fixed): product page, category page with marquee, filters and histogram, search results, compare, signup, all checkout steps, Razorpay page, success, track, invoice, account, 404, 429, mobile layouts.

Acceptance rule for every finding: it is closed only with evidence (a real command output, test, or before/after screenshot named in the report). Create docs/ui-review/ for before/after images.
