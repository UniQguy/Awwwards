/**
 * Quantity stepper enhancement for shopping bag line items.
 */
export function initQuantityStepper() {
  const steppers = document.querySelectorAll(".quantity-stepper");
  steppers.forEach((stepper) => {
    const input = stepper.querySelector(".stepper-input");
    const minusBtn = stepper.querySelector("[data-step-down]");
    const plusBtn = stepper.querySelector("[data-step-up]");
    if (!input || !minusBtn || !plusBtn) return;

    minusBtn.addEventListener("click", (e) => {
      // In JS-enabled mode, prevent native form submission if present and change input
      const current = parseInt(input.value, 10) || 1;
      const min = parseInt(input.min, 10) || 0;
      if (current > min) {
        input.value = current - 1;
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });

    plusBtn.addEventListener("click", (e) => {
      const current = parseInt(input.value, 10) || 1;
      const max = parseInt(input.max, 10) || 10;
      if (current < max) {
        input.value = current + 1;
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
  });
}
