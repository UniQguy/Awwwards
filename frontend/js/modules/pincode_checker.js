/**
 * Live inline pincode checker with instant tick (✓) or cross (✕).
 * Prevents page reload/jumps. Triggers on typing 6 digits or clicking Check.
 */
export function initPincodeChecker() {
  const forms = document.querySelectorAll(".pincode-live-form");
  if (!forms.length) return;

  forms.forEach((form) => {
    const input = form.querySelector(".pincode-live-input");
    const container = form.closest(".pincode-inline-box, .product-pincode-inline");
    const resultContainer = container ? container.querySelector(".pincode-live-result") : null;

    if (!input) return;

    let abortController = null;

    async function checkPincode(pin) {
      pin = (pin || "").trim();
      if (!pin || pin.length !== 6 || !/^[1-9][0-9]{5}$/.test(pin)) {
        if (resultContainer) {
          resultContainer.innerHTML = `
            <span class="badge badge-danger text-xs font-mono inline-flex items-center gap-1.5 py-1 px-2.5" style="background: rgba(239, 68, 68, 0.12); color: #dc2626; border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 4px;">
              <span>✕</span>
              <span>Service unavailable for PIN ${pin || "N/A"} (Please enter a valid 6-digit Indian pincode)</span>
            </span>
          `;
        }
        return;
      }

      if (abortController) {
        abortController.abort();
      }
      abortController = new AbortController();

      try {
        const response = await fetch(`/shipping/estimate/?pincode=${encodeURIComponent(pin)}`, {
          method: "GET",
          headers: {
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
          signal: abortController.signal,
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (resultContainer) {
          if (data.serviceable) {
            resultContainer.innerHTML = `
              <span class="badge badge-success text-xs font-mono inline-flex items-center gap-1.5 py-1 px-2.5" style="background: rgba(16, 185, 129, 0.12); color: #059669; border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 4px;">
                <span>${data.message || `✓ Deliverable to (${pin}) — Estimated delivery in 2–4 days • COD & Express Available`}</span>
              </span>
            `;
          } else {
            resultContainer.innerHTML = `
              <span class="badge badge-danger text-xs font-mono inline-flex items-center gap-1.5 py-1 px-2.5" style="background: rgba(239, 68, 68, 0.12); color: #dc2626; border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 4px;">
                <span>${data.message || `✕ Service unavailable for PIN ${pin} (Please enter a valid 6-digit Indian pincode)`}</span>
              </span>
            `;
          }
        }
      } catch (err) {
        if (err.name === "AbortError") return;
        if (resultContainer) {
          resultContainer.innerHTML = `
            <span class="badge badge-danger text-xs font-mono inline-flex items-center gap-1.5 py-1 px-2.5" style="background: rgba(239, 68, 68, 0.12); color: #dc2626; border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 4px;">
              <span>✕ Service unavailable for PIN ${pin} (Please enter a valid 6-digit Indian pincode)</span>
            </span>
          `;
        }
      }
    }

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      checkPincode(input.value);
    });

    input.addEventListener("input", () => {
      const val = input.value.trim();
      if (val.length === 6) {
        checkPincode(val);
      }
    });
  });
}
