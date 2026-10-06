/**
 * Progressive image error fallback handler.
 * Swaps broken images with an editorial CSS/SVG plinth without layout shift.
 */
export function initImageFallback() {
  const images = document.querySelectorAll(".product-plate img");
  images.forEach((img) => {
    // If already broken
    if (img.complete && img.naturalWidth === 0) {
      applyFallback(img);
    } else {
      img.addEventListener("error", () => applyFallback(img), { once: true });
    }
  });
}

function applyFallback(img) {
  const plate = img.closest(".product-plate");
  if (!plate) return;

  img.style.display = "none";
  const existingFallback = plate.querySelector(".image-fallback-plate");
  if (!existingFallback) {
    const fallback = document.createElement("div");
    fallback.className = "image-fallback-plate";
    fallback.setAttribute("role", "img");
    fallback.setAttribute("aria-label", img.alt || "Product image unavailable");
    fallback.innerHTML = `
      <span class="image-fallback-initial">E</span>
      <span class="image-fallback-text">Image unavailable</span>
    `;
    plate.appendChild(fallback);
  } else {
    existingFallback.style.display = "flex";
  }
}
