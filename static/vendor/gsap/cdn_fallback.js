/**
 * Vendored fallback loader for GSAP & ScrollTrigger (WP7).
 * Checks for window.gsap after 2500ms.
 * If missing (due to network failure, CDN blocking, or SRI mismatch),
 * injects the local vendored copies from /static/vendor/gsap/.
 */
(function () {
  setTimeout(function () {
    if (typeof window.gsap === "undefined") {
      console.warn("GSAP CDN unavailable or blocked. Injecting local vendored fallback.");
      var script1 = document.createElement("script");
      script1.src = "/static/vendor/gsap/gsap.min.js";
      script1.onload = function () {
        if (typeof window.ScrollTrigger === "undefined") {
          var script2 = document.createElement("script");
          script2.src = "/static/vendor/gsap/ScrollTrigger.min.js";
          script2.onload = function () {
            if (window.gsap && window.ScrollTrigger) {
              window.gsap.registerPlugin(window.ScrollTrigger);
              window.ScrollTrigger.config({ syncInterval: 99999999 });
              window.dispatchEvent(new CustomEvent("gsap:ready"));
            }
          };
          document.head.appendChild(script2);
        }
      };
      document.head.appendChild(script1);
    } else if (typeof window.ScrollTrigger === "undefined") {
      var script2 = document.createElement("script");
      script2.src = "/static/vendor/gsap/ScrollTrigger.min.js";
      script2.onload = function () {
        if (window.gsap && window.ScrollTrigger) {
          window.gsap.registerPlugin(window.ScrollTrigger);
          window.ScrollTrigger.config({ syncInterval: 99999999 });
          window.dispatchEvent(new CustomEvent("gsap:ready"));
        }
      };
      document.head.appendChild(script2);
    } else {
      if (window.gsap && window.ScrollTrigger) {
        window.gsap.registerPlugin(window.ScrollTrigger);
        window.ScrollTrigger.config({ syncInterval: 99999999 });
      }
    }
  }, 2500);
})();
