/**
 * Header scroll shadow elevation, scroll progress thread, and editorial world color syncing.
 */
export function initHeaderScroll() {
  const header = document.querySelector(".site-header");
  const sentinel = document.querySelector("#header-sentinel");
  const progressThread = document.querySelector("#header-progress-thread");

  if (!header) return;

  // 1. Elevation shadow on scroll past sentinel
  if (sentinel) {
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

  // 2. Active World tracking for editorial pages
  const chapterElements = document.querySelectorAll("[data-world], .chapter-section[data-accent]");
  if (chapterElements.length > 0 && typeof IntersectionObserver !== "undefined") {
    const worldObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const worldKey = entry.target.getAttribute("data-world") || entry.target.getAttribute("data-accent");
            if (worldKey) {
              header.setAttribute("data-world", worldKey);
              // Also sync CSS variable if defined on target
              const targetStyle = window.getComputedStyle(entry.target);
              const accentColor = targetStyle.getPropertyValue("--world-accent").trim();
              if (accentColor && progressThread) {
                progressThread.style.backgroundColor = accentColor;
              }
            }
          }
        });
      },
      { rootMargin: "-72px 0px -40% 0px", threshold: 0.1 }
    );

    chapterElements.forEach((el) => worldObserver.observe(el));
  }

  // 3. Scroll progress thread along bottom edge of header
  if (progressThread) {
    let ticking = false;
    const updateProgress = () => {
      const scrollY = window.scrollY || window.pageYOffset;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = docHeight > 0 ? Math.min(100, Math.max(0, (scrollY / docHeight) * 100)) : 0;
      progressThread.style.width = `${progress}%`;
      ticking = false;
    };

    window.addEventListener("scroll", () => {
      if (!ticking) {
        window.requestAnimationFrame(updateProgress);
        ticking = true;
      }
    }, { passive: true });

    updateProgress();
  }
}
