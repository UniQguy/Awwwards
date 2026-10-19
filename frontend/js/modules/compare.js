/**
 * Product Specification Comparison Matrix Controller (Phase R10, Pillar 2).
 * Handles:
 * - Differences toggle without inline handlers
 * - Dynamic + Add Product dropdown picker
 */

export function initComparePage() {
  const table = document.getElementById("compare-matrix-table");
  const toggleBtn = document.getElementById("toggle-diffs-btn");

  if (toggleBtn && table) {
    toggleBtn.addEventListener("click", () => {
      table.classList.toggle("show-only-diffs");
      if (table.classList.contains("show-only-diffs")) {
        toggleBtn.textContent = "Show All Specs";
        toggleBtn.classList.add("btn-primary");
        toggleBtn.classList.remove("btn-secondary");
      } else {
        toggleBtn.textContent = "Show Only Differences";
        toggleBtn.classList.add("btn-secondary");
        toggleBtn.classList.remove("btn-primary");
      }
    });
  }

  const selectEl = document.getElementById("compare-product-select");
  const formEl = document.getElementById("compare-add-picker-form");
  const submitBtn = document.getElementById("compare-add-picker-submit");

  if (selectEl && formEl) {
    selectEl.addEventListener("change", () => {
      const val = selectEl.value;
      if (submitBtn) {
        submitBtn.disabled = !val;
      }
      if (val) {
        formEl.action = `/compare/add/${val}/`;
      }
    });
  }
}
