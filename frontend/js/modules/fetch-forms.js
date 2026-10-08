/**
 * Progressive enhancement for instant action forms (Add to bag, wishlist, compare).
 * Submits via fetch with JSON headers and announces result politely to assistive tech.
 * Falls back transparently to standard native POST form submission on any network or parsing error.
 */
export function initFetchForms() {
  const forms = document.querySelectorAll("form[data-fetch-enhance]");

  forms.forEach((form) => {
    form.addEventListener("submit", async (e) => {
      // Cart update forms are handled live by quantity-stepper module
      if (form.action.includes("/cart/update/")) {
        return;
      }

      e.preventDefault();

      const csrfInput = form.querySelector("input[name='csrfmiddlewaretoken']");
      const csrfToken = csrfInput ? csrfInput.value : "";
      const formData = new FormData(form);

      const submitBtn = form.querySelector("button[type='submit']");
      if (submitBtn) {
        submitBtn.setAttribute("aria-busy", "true");
      }

      try {
        const response = await fetch(form.action, {
          method: "POST",
          headers: {
            "Accept": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // 1. Update Bag count in header with 160ms vertical slide tick
        if (typeof data.cart_count === "number") {
          const badge = document.querySelector(".header-bag-link .bag-badge");
          if (badge) {
            badge.textContent = `(${data.cart_count})`;
            badge.classList.remove("badge-tick");
            void badge.offsetWidth; // trigger reflow
            badge.classList.add("badge-tick");
            setTimeout(() => badge.classList.remove("badge-tick"), 300);
          }
        }

        // 2. Button state: tick and "Added", stays 900ms, reverts
        if (data.success && submitBtn) {
          submitBtn.removeAttribute("aria-busy");
          const originalHTML = submitBtn.innerHTML;
          submitBtn.innerHTML = `&check; Added`;
          setTimeout(() => {
            submitBtn.innerHTML = originalHTML;
          }, 900);
        } else if (submitBtn) {
          submitBtn.removeAttribute("aria-busy");
        }

        // 3. Announce message politely via ARIA live region
        const announcer = document.querySelector("#live-announcer");
        if (announcer) {
          const subtotalText = data.summary ? data.summary.formatted_subtotal : "";
          const itemCount = typeof data.cart_count === "number" ? data.cart_count : "";
          announcer.textContent = `Added to bag. ${itemCount} items in bag, subtotal ${subtotalText}.`;
        }

        // 4. Slide-over mini-bag drawer (<dialog>)
        if (data.success && data.item) {
          openMiniBagDrawer(data);
        }
      } catch (err) {
        // Transparent fallback: submit natively without JavaScript interference
        if (submitBtn) submitBtn.removeAttribute("aria-busy");
        form.submit();
      }
    });
  });
}

/**
 * Populates and reveals the native <dialog> mini-bag slide-over drawer.
 *
 * @param {Object} data - Cart JSON response payload
 */
export function openMiniBagDrawer(data) {
  const dialog = document.getElementById("mini-bag-dialog");
  if (!dialog) return;

  const countBadge = document.getElementById("mini-bag-count-badge");
  const thumbImg = document.getElementById("mini-bag-thumb-img");
  const nameEl = document.getElementById("mini-bag-item-name");
  const qtyEl = document.getElementById("mini-bag-item-qty");
  const priceEl = document.getElementById("mini-bag-item-price");
  const meterFill = document.getElementById("mini-bag-meter-fill");
  const meterLabel = document.getElementById("mini-bag-meter-label");
  const subtotalEl = document.getElementById("mini-bag-subtotal-val");

  if (countBadge && typeof data.cart_count === "number") {
    countBadge.textContent = `(${data.cart_count})`;
  }
  if (thumbImg && data.item) {
    thumbImg.src = data.item.image_url || "";
    thumbImg.alt = data.item.name || "";
  }
  if (nameEl && data.item) {
    nameEl.textContent = data.item.name || "";
  }
  if (qtyEl && data.item) {
    qtyEl.textContent = data.item.quantity || "1";
  }
  if (priceEl && data.item) {
    priceEl.textContent = data.item.formatted_price || "";
  }
  if (subtotalEl && data.summary) {
    subtotalEl.textContent = data.summary.formatted_subtotal || "";
  }
  if (data.summary) {
    if (meterFill) {
      meterFill.style.width = `${data.summary.free_shipping_progress}%`;
    }
    if (meterLabel) {
      if (data.summary.free_shipping_qualified) {
        meterLabel.innerHTML = `<strong class="text-success">&check; You have qualified for free delivery.</strong>`;
      } else {
        meterLabel.innerHTML = `Add <strong>${data.summary.formatted_free_shipping_remaining}</strong> more for <strong>FREE delivery</strong>`;
      }
    }
  }

  // Setup close handlers once
  if (!dialog.dataset.wired) {
    dialog.dataset.wired = "1";
    const closeBtn = document.getElementById("mini-bag-close-btn");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => dialog.close());
    }
    dialog.addEventListener("click", (evt) => {
      const panel = dialog.querySelector(".mini-bag-panel");
      if (panel) {
        const rect = panel.getBoundingClientRect();
        const isInPanel = (
          evt.clientX >= rect.left && evt.clientX <= rect.right &&
          evt.clientY >= rect.top && evt.clientY <= rect.bottom
        );
        if (!isInPanel) {
          dialog.close();
        }
      }
    });
  }

  try {
    dialog.showModal();
    const closeBtn = document.getElementById("mini-bag-close-btn");
    if (closeBtn) {
      closeBtn.focus();
    }
  } catch (_) {}
}
