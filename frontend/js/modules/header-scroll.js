/**
 * Header scroll shadow elevation using IntersectionObserver sentinel.
 * Avoids window scroll event listeners for 60fps rendering.
 */
export function initHeaderScroll() {
  const header = document.querySelector(".site-header");
  const sentinel = document.querySelector("#header-sentinel");
  if (!header || !sentinel) return;

  const observer = new IntersectionObserver(
    ([entry]) => {
      if (!entry.isIntersecting) {
        header.classList.add("is-scrolled");
      } else {
        header.classList.remove("is-scrolled");
      }
    },
    { threshold: 0 }
  );

  observer.observe(sentinel);
}
