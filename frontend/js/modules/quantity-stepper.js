/**
 * Quantity stepper progressive enhancement for shopping bag line items.
 * Recalculates live with fetch, cross-fades line and total amounts (120ms),
 * and updates the free-shipping progress meter without full page reload.
 */
export function initQuantityStepper() {
  const steppers = document.querySelectorAll(".quantity-stepper");

  steppers.forEach((stepper) => {
    const input = stepper.querySelector(".stepper-input");
    const minusBtn = stepper.querySelector("[data-step-down]");
    const plusBtn = stepper.querySelector("[data-step-up]");
    const form = stepper.closest("form");
    if (!input || !minusBtn || !plusBtn || !form) return;

    // Intercept form submit if submitted manually via "Update" button
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      triggerLiveUpdate(form, input.value);
    });

    minusBtn.addEventListener("click", (e) => {
      e.preventDefault();
      const current = parseInt(input.value, 10) || 1;
      const min = parseInt(input.min, 10) || 1;
      if (current > min) {
        input.value = current - 1;
        triggerLiveUpdate(form, input.value);
      }
    });

    plusBtn.addEventListener("click", (e) => {
      e.preventDefault();
      const current = parseInt(input.value, 10) || 1;
      const max = parseInt(input.max, 10) || 10;
      if (current < max) {
        input.value = current + 1;
        triggerLiveUpdate(form, input.value);
      }
    });

    input.addEventListener("change", () => {
      triggerLiveUpdate(form, input.value);
    });
  });
}

let updateDebounceTimer = null;

/**
 * Executes live fetch for cart line item updates and crossfades updated values.
 *
 * @param {HTMLFormElement} form
 * @param {number|string} quantity
 */
async function triggerLiveUpdate(form, quantity) {
  if (updateDebounceTimer) {
    clearTimeout(updateDebounceTimer);
  }

  const lineItem = form.closest(".cart-line-item");
  const linePrice = lineItem?.querySelector(".price");
  const subtotalEl = document.querySelector(".summary-totals-dl dd");
  const grandTotalEl = document.querySelector(".summary-grand-total .total-amount");
  const meterFill = document.querySelector(".meter-progress-fill");
  const meterLabel = document.querySelector(".meter-label-row");
  const bagBadge = document.querySelector(".header-bag-link .bag-badge");
  const csrfInput = form.querySelector("input[name='csrfmiddlewaretoken']");
  const csrfToken = csrfInput ? csrfInput.value : "";

  // Apply crossfade dimming (120ms transition)
  if (linePrice) linePrice.classList.add("fade-updating");
  if (subtotalEl) subtotalEl.classList.add("fade-updating");
  if (grandTotalEl) grandTotalEl.classList.add("fade-updating");

  updateDebounceTimer = setTimeout(async () => {
    try {
      const formData = new FormData();
      formData.append("quantity", String(quantity));
      if (csrfToken) formData.append("csrfmiddlewaretoken", csrfToken);

      const res = await fetch(form.action, {
        method: "POST",
        headers: {
          "Accept": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: formData,
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();

      if (data.success) {
        // Cross-fade text updates
        setTimeout(() => {
          if (data.item_removed && lineItem) {
            lineItem.remove();
          } else if (linePrice) {
            linePrice.textContent = data.formatted_line_subtotal;
          }

          if (data.summary) {
            if (subtotalEl) subtotalEl.textContent = data.summary.formatted_subtotal;
            if (grandTotalEl) grandTotalEl.textContent = data.summary.formatted_grand_total;

            if (meterFill) {
              meterFill.style.width = `${data.summary.free_shipping_progress}%`;
            }
            if (meterLabel) {
              if (data.summary.free_shipping_progress >= 100) {
                meterLabel.innerHTML = `
                  <strong class="text-success">&check; You have qualified for free delivery.</strong>
                  <span class="caption">Threshold: ₹499</span>
                `;
              } else {
                meterLabel.innerHTML = `
                  <span>Add <strong>${data.summary.formatted_free_shipping_remaining}</strong> more to qualify for <strong>FREE delivery</strong></span>
                  <span class="caption">Threshold: ₹499</span>
                `;
              }
            }
          }

          // Header bag badge tick
          if (bagBadge && typeof data.cart_count === "number") {
            bagBadge.textContent = `(${data.cart_count})`;
            bagBadge.classList.remove("badge-tick");
            void bagBadge.offsetWidth;
            bagBadge.classList.add("badge-tick");
            setTimeout(() => bagBadge.classList.remove("badge-tick"), 300);
          }

          // Restore opacity
          if (linePrice) linePrice.classList.remove("fade-updating");
          if (subtotalEl) subtotalEl.classList.remove("fade-updating");
          if (grandTotalEl) grandTotalEl.classList.remove("fade-updating");
        }, 120);
      }
    } catch (err) {
      // Revert fading and submit natively
      if (linePrice) linePrice.classList.remove("fade-updating");
      if (subtotalEl) subtotalEl.classList.remove("fade-updating");
      if (grandTotalEl) grandTotalEl.classList.remove("fade-updating");
      form.submit();
    }
  }, 150);
}
