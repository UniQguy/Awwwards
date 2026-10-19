/**
 * AI Concierge & Technical Assistant Controller (Phase R10, Pillar 6).
 * Handles floating launcher, chat drawer, prompt suggestions, and JSON communication.
 */

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);

  // Bold: **text**
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  // Code: `code`
  html = html.replace(/`([^`]+)`/g, "<code class='font-mono text-2xs'>$1</code>");

  // Bullet items: - item
  const lines = html.split("\n");
  let inList = false;
  let formattedLines = [];

  for (let line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ")) {
      if (!inList) {
        formattedLines.push("<ul>");
        inList = true;
      }
      formattedLines.push(`<li>${trimmed.slice(2)}</li>`);
    } else {
      if (inList) {
        formattedLines.push("</ul>");
        inList = false;
      }
      if (trimmed.length > 0) {
        formattedLines.push(`<p>${trimmed}</p>`);
      }
    }
  }
  if (inList) {
    formattedLines.push("</ul>");
  }

  return formattedLines.join("");
}

export function initAiConcierge() {
  const launcherBtn = document.getElementById("concierge-launcher-btn");
  const drawer = document.getElementById("concierge-drawer");
  const closeBtn = document.getElementById("concierge-close-btn");
  const messagesContainer = document.getElementById("concierge-messages");
  const typingIndicator = document.getElementById("concierge-typing");
  const form = document.getElementById("concierge-form");
  const input = document.getElementById("concierge-input");

  if (!launcherBtn || !drawer || !form || !input) return;

  function openDrawer() {
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    launcherBtn.setAttribute("aria-expanded", "true");
    input.focus();
  }

  function closeDrawer() {
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    launcherBtn.setAttribute("aria-expanded", "false");
    launcherBtn.focus();
  }

  launcherBtn.addEventListener("click", () => {
    if (drawer.classList.contains("is-open")) {
      closeDrawer();
    } else {
      openDrawer();
    }
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", closeDrawer);
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && drawer.classList.contains("is-open")) {
      closeDrawer();
    }
  });

  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  function appendUserMessage(text) {
    const bubble = document.createElement("div");
    bubble.className = "concierge-bubble is-user";
    bubble.textContent = text;
    if (typingIndicator) {
      messagesContainer.insertBefore(bubble, typingIndicator);
    } else {
      messagesContainer.appendChild(bubble);
    }
    scrollToBottom();
  }

  function appendAssistantResponse(data) {
    const bubble = document.createElement("div");
    bubble.className = "concierge-bubble is-assistant";

    const contentDiv = document.createElement("div");
    contentDiv.innerHTML = formatMarkdown(data.reply);
    bubble.appendChild(contentDiv);

    // Render product recommendation cards
    if (Array.isArray(data.products) && data.products.length > 0) {
      const prodsWrapper = document.createElement("div");
      prodsWrapper.className = "mt-3 flex flex-col gap-2";

      data.products.forEach((prod) => {
        const card = document.createElement("a");
        card.href = prod.url;
        card.className = "concierge-product-card";

        const img = document.createElement("img");
        img.src = prod.image_url || "/static/images/placeholder.png";
        img.alt = prod.name;
        img.className = "concierge-prod-img";
        img.loading = "lazy";

        const info = document.createElement("div");
        info.className = "concierge-prod-info";

        const title = document.createElement("div");
        title.className = "concierge-prod-title";
        title.textContent = prod.name;

        const priceRow = document.createElement("div");
        priceRow.className = "flex items-center gap-2 flex-wrap";

        const price = document.createElement("span");
        price.className = "concierge-prod-price";
        price.textContent = prod.formatted_price;
        priceRow.appendChild(price);

        if (prod.effective_price && prod.coupon_code) {
          const dealBadge = document.createElement("span");
          dealBadge.className = "badge badge-coupon-deal text-3xs font-mono";
          dealBadge.textContent = `As low as ${prod.effective_price}`;
          priceRow.appendChild(dealBadge);
        }

        info.appendChild(title);
        info.appendChild(priceRow);

        card.appendChild(img);
        card.appendChild(info);
        prodsWrapper.appendChild(card);
      });

      bubble.appendChild(prodsWrapper);
    }

    // Render coupon copy pills
    if (Array.isArray(data.coupons) && data.coupons.length > 0) {
      const couponRow = document.createElement("div");
      couponRow.className = "mt-3 flex flex-wrap gap-1.5";

      data.coupons.forEach((c) => {
        const pill = document.createElement("button");
        pill.type = "button";
        pill.className = "concierge-coupon-pill";
        pill.innerHTML = `<span>${escapeHtml(c.code)}</span> <span class="caption text-muted font-normal text-3xs">${escapeHtml(c.discount_label)}</span>`;
        pill.title = "Click to copy promo code";

        pill.addEventListener("click", () => {
          navigator.clipboard.writeText(c.code).then(() => {
            pill.textContent = "Copied";
            setTimeout(() => {
              pill.innerHTML = `<span>${escapeHtml(c.code)}</span> <span class="caption text-muted font-normal text-3xs">${escapeHtml(c.discount_label)}</span>`;
            }, 1800);
          });
        });

        couponRow.appendChild(pill);
      });

      bubble.appendChild(couponRow);
    }

    // Render actions
    if (Array.isArray(data.actions) && data.actions.length > 0) {
      const actionsRow = document.createElement("div");
      actionsRow.className = "mt-3 flex flex-wrap gap-2 pt-2 hairline-top";

      data.actions.forEach((act) => {
        const link = document.createElement("a");
        link.href = act.url;
        link.className = "btn btn-secondary btn-xs";
        link.textContent = act.label;
        actionsRow.appendChild(link);
      });

      bubble.appendChild(actionsRow);
    }

    if (typingIndicator) {
      messagesContainer.insertBefore(bubble, typingIndicator);
    } else {
      messagesContainer.appendChild(bubble);
    }
    scrollToBottom();
  }

  async function sendMessage(text) {
    if (!text || !text.trim()) return;
    const cleanText = text.trim();

    appendUserMessage(cleanText);
    input.value = "";

    if (typingIndicator) {
      typingIndicator.classList.remove("hidden");
      typingIndicator.removeAttribute("aria-hidden");
    }
    scrollToBottom();

    // CSRF token
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";

    try {
      const res = await fetch("/api/assistant/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ message: cleanText }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      if (typingIndicator) {
        typingIndicator.classList.add("hidden");
        typingIndicator.setAttribute("aria-hidden", "true");
      }
      appendAssistantResponse(data);
    } catch (err) {
      if (typingIndicator) {
        typingIndicator.classList.add("hidden");
        typingIndicator.setAttribute("aria-hidden", "true");
      }
      appendAssistantResponse({
        reply: "I encountered a network issue communicating with the assistant service. Please check your connection or contact customer support directly at /support/.",
        products: [],
        coupons: [],
        actions: [
          {"label": "Contact Support", "url": "/support/"},
        ],
      });
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const val = input.value;
    sendMessage(val);
  });

  // Quick prompt chips
  document.querySelectorAll(".concierge-chip-btn").forEach((chip) => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      if (prompt) {
        sendMessage(prompt);
      }
    });
  });
}
