/**
 * Progressive enhancement for instant action forms (Add to bag, wishlist, compare).
 * Submits via fetch with JSON headers and announces result politely to assistive tech.
 * Falls back transparently to standard native POST form submission on any network or parsing error.
 */
export function initFetchForms() {
  const forms = document.querySelectorAll("form[data-fetch-enhance]");

  forms.forEach((form) => {
    form.addEventListener("submit", async (e) => {
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

        // Update Bag count if provided
        if (typeof data.cart_count === "number") {
          const badge = document.querySelector(".bag-badge");
          if (badge) {
            badge.textContent = `(${data.cart_count})`;
          }
        }

        // Announce message politely via ARIA live region
        const announcer = document.querySelector("#live-announcer");
        if (announcer && data.message) {
          announcer.textContent = data.message;
        }

        // Trigger custom UI feedback if defined
        if (data.success && submitBtn) {
          submitBtn.removeAttribute("aria-busy");
          const originalText = submitBtn.textContent;
          submitBtn.textContent = "Added";
          setTimeout(() => {
            submitBtn.textContent = originalText;
          }, 1500);
        } else if (submitBtn) {
          submitBtn.removeAttribute("aria-busy");
        }
      } catch (err) {
        // Transparent fallback: submit natively without JavaScript interference
        if (submitBtn) submitBtn.removeAttribute("aria-busy");
        form.submit();
      }
    });
  });
}
