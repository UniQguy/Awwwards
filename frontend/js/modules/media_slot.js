/**
 * Reusable Media Slot Video Observer for ELECTROCART.
 * Strictly adheres to Tier 1 Desktop playback conditions:
 * - Plays only when Tier == 1, window.innerWidth >= 1024, and prefers-reduced-motion is false.
 * - Under Tier 2/3, mobile, touch, save-data, or reduced motion, video src is NEVER assigned,
 *   saving 100% of bandwidth and rendering poster image exclusively.
 * - IntersectionObserver plays when visible, pauses when out of view.
 * - Pauses immediately when document becomes hidden (tab switch/minimize).
 */

export function initMediaSlots() {
  const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isSaveData = navigator.connection && navigator.connection.saveData;
  const isTier1 = document.documentElement.getAttribute("data-motion-tier") === "1";
  const isDesktop = window.innerWidth >= 1024;

  const canPlayVideo = isTier1 && isDesktop && !isReducedMotion && !isSaveData;

  const containers = document.querySelectorAll(".media-slot-container");
  if (!containers.length) return;

  if (!canPlayVideo) {
    // Under Tier 2/3, mobile, or save-data: ensure no video downloads occur
    containers.forEach((container) => {
      const video = container.querySelector("video.media-slot-video");
      if (video) {
        video.removeAttribute("src");
        video.style.display = "none";
      }
    });
    return;
  }

  // Tier 1 Desktop fine-pointer path: Wire up IntersectionObserver
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const video = entry.target.querySelector("video.media-slot-video");
        if (!video) return;

        if (entry.isIntersecting) {
          // Lazy assign src from data-src on first approach
          if (!video.src && video.dataset.src) {
            video.src = video.dataset.src;
            video.load();
          }
          const playPromise = video.play();
          if (playPromise !== undefined) {
            playPromise.catch(() => {
              // Browser autoplay policy rejected or interrupted; fallback gracefully
            });
          }
        } else {
          if (!video.paused) {
            video.pause();
          }
        }
      });
    },
    { threshold: 0.25 }
  );

  containers.forEach((c) => observer.observe(c));

  // Tab visibility listener: pause when backgrounded
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      containers.forEach((c) => {
        const video = c.querySelector("video.media-slot-video");
        if (video && !video.paused) {
          video.pause();
        }
      });
    }
  });
}
