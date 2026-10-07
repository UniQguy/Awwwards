/**
 * Mobile sticky purchase bar observer.
 * Shows sticky bottom bar when main product purchase button scrolls out of view.
 */
export function initStickyPurchaseBar() {
  const bar = document.querySelector("[data-sticky-bar]");
  const mainBtn = document.querySelector(".product-purchase-box button[type='submit']");
  if (!bar || !mainBtn || !("IntersectionObserver" in window)) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting && entry.boundingClientRect.top < 0) {
          bar.classList.add("is-visible");
        } else {
          bar.classList.remove("is-visible");
        }
      });
    },
    { threshold: 0 }
  );

  observer.observe(mainBtn);
}
