# ELECTROCART VOICE & MICROCOPY DECK

**North Star**: Warm, plain, exact, a little literary, never salesy. Short sentences. Say what is true.

---

## 1. Principles

1. **Say what is true**:
   - Never exaggerate. No hype words ("amazing", "best", "unbeatable", "premium", "revolutionary").
   - State facts, rates, specifications, and delivery timelines directly.
   - Plainly acknowledge sample data and test modes: *"Catalogue prices come from an older sample dataset and stock levels are sample data."*

2. **No false urgency or scarcity games**:
   - Zero exclamation marks in notifications and system notices.
   - Zero countdown timers or flashing alerts.
   - Stock counts reflect verified warehouse stock: *"Only 3 left in stock."* or *"In stock."*
   - Out of stock is calm and honest: *"Out of stock for now."*

3. **Consistent Naming**:
   - Customer UI uses **Bag** consistently (*"Shopping Bag"*, *"Add to bag"*, *"Your bag is empty"*).
   - Python code, endpoints, and models preserve **Cart** (`Cart`, `apps.cart`, `/cart/`) to avoid churn.

4. **Verbs on Actions**:
   - Button text starts with direct verbs: *"Add to bag"*, *"Review order"*, *"Place order"*, *"Track order"*, *"Save address"*, *"Apply code"*.

---

## 2. Canonical UI Strings

### A. Shopping Bag & Free Delivery
- **Empty Bag**: *"Your bag is empty. Everything you add will wait here."*
- **Action on Empty**: *"Explore catalog"*
- **Threshold Progress**: *"{amount} more and delivery is free."*
- **Threshold Qualified**: *"Delivery is free on this order."*
- **Threshold Threshold Note**: *"Free delivery on orders over ₹499."*
- **Add to Bag Button**: *"Add to bag"*
- **Item Added Confirmation**: *"Added {name} to your bag."*
- **Clamped Quantity**: *"Adjusted quantity to {count} units based on available stock."*

### B. Shipping, Delivery & PIN Codes
- **PIN Prompt**: *"Enter 6-digit PIN code"*
- **PIN Check Button**: *"Check delivery"*
- **Serviceable Estimate**: *"Delivery in {min} to {max} business days ({dates})."*
- **Unserviceable PIN**: *"We can't deliver to this PIN code yet."*
- **No Estimate Available**: *"Delivery estimate unavailable for this PIN."*
- **COD Permitted**: *"Cash on delivery available."*
- **COD Restricted**: *"Online payment only for this destination."*

### C. Promotional Codes
- **Input Placeholder**: *"Discount code"*
- **Apply Button**: *"Apply code"*
- **Valid Code**: *"Code '{code}' applied. Saved {amount}."*
- **Expired Code**: *"That code has expired."*
- **Invalid Code**: *"That code was not recognized."*
- **Min Threshold Unmet**: *"Add {amount} more to apply this code."*
- **Remove Code**: *"Remove code"*

### D. Checkout & Stock Holds
- **Stock Hold Notice**: *"Items in your bag are held for {minutes} minutes while you complete checkout."*
- **Guest Step**: *"Continue as guest or sign in for saved addresses."*
- **Address Choice**: *"Select delivery address"*
- **Review Step**: *"Review your order"*
- **Place COD Order**: *"Place order with Cash on Delivery"*
- **Place Online Order**: *"Continue to payment"*

### E. Post-Purchase & Tracking
- **Order Success Title**: *"Order received"*
- **Order Success Subhead**: *"We have begun preparing order {order_number}."*
- **Invoice Link**: *"Download Tax Invoice"* / *"Download Bill of Supply"*
- **Guest Bookmark Prompt**: *"Save this link to check progress anytime."*
- **Timeline Milestones**:
  - Confirmed: *"Order confirmed"*
  - Processing: *"Preparing for dispatch"*
  - Shipped: *"Dispatched with logistics carrier"*
  - Delivered: *"Delivered"*
  - Cancelled: *"Order cancelled and inventory released"*

### F. Payment Statuses
- **Payment Failed**: *"The payment didn't go through. You can try again or pay on delivery."*
- **Payment Cancelled**: *"Payment was cancelled. Your items remain in your bag."*
- **Payment Pending**: *"Your payment is processing with the bank. We will confirm shortly."*

### G. Error Pages & Empty States
- **404 Not Found**:
  - Title: *"Page not found"*
  - Sentence: *"This page isn't here. Perhaps it was moved, or never was."*
  - Action: *"Return to catalog"*
- **500 Server Error**:
  - Title: *"Service temporarily unavailable"*
  - Sentence: *"We encountered an unexpected error on our server. Our team has been alerted."*
- **403 Forbidden**:
  - Title: *"Access restricted"*
  - Sentence: *"You don't have permission to view this resource."*
- **429 Too Many Requests**:
  - Title: *"Too many requests"*
  - Sentence: *"Please pause for a moment before trying again."*
- **Empty Search**:
  - Title: *"No products matched your query"*
  - Sentence: *"Try checking your spelling or searching for a general hardware category."*
- **Empty Wishlist**:
  - Title: *"Your saved list is empty"*
  - Sentence: *"Items you bookmark while browsing will appear here."*
