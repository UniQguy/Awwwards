/**
 * Progressive Enhancement: Image Error Fallback.
 * Loaded with defer. Replaces failed external marketplace images with clean monograph fallback.
 */
document.addEventListener("DOMContentLoaded", function () {
    var images = document.querySelectorAll("img.product-img");
    images.forEach(function (img) {
        img.addEventListener("error", function () {
            var cat = img.getAttribute("data-category") || "Electronics";
            var fallback = document.createElement("div");
            fallback.className = "image-fallback-plate";
            fallback.setAttribute("role", "img");
            fallback.setAttribute("aria-label", img.alt || "Product image unavailable");
            fallback.innerHTML = "<span class='fallback-title'>Image Unavailable</span><span class='fallback-category'>" + cat + "</span>";
            if (img.parentNode) {
                img.parentNode.replaceChild(fallback, img);
            }
        });
    });
});
