(function () {
  const downloads = window.__PULSE_DOWNLOADS__ || {};
  const recommendationMap = {
    windows: {
      headline: "Windows native wrapper",
      message: downloads.windows && downloads.windows.available
        ? "Download the .scr package for the cleanest install path with native preview and full-screen playback."
        : "Windows detected. The .scr release is not attached here yet, so use the ZIP bundle or run the browser build.",
    },
    macos: {
      headline: "macOS screen saver bundle",
      message: downloads.macos && downloads.macos.available
        ? "Download the .saver package for System Settings installation and native preview support."
        : "macOS detected. The .saver release is not attached here yet, so use the ZIP bundle or run the browser build.",
    },
    linux: {
      headline: "Universal offline bundle",
      message: "Linux detected. The ZIP bundle is the reliable offline path and works with kiosk or wrapper hosts.",
    },
    browser: {
      headline: "Run instantly in browser",
      message: "If you want immediate playback, launch the bundled browser build and let the screensaver runtime handle the rest.",
    },
    unknown: {
      headline: "Universal offline bundle",
      message: "We could not confidently identify your OS, so the ZIP bundle is the safest offline option.",
    },
  };

  function detectOs() {
    const platform = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "";
    const userAgent = navigator.userAgent || "";
    const sample = `${platform} ${userAgent}`.toLowerCase();

    if (sample.includes("win")) return "windows";
    if (sample.includes("mac") || sample.includes("darwin")) return "macos";
    if (sample.includes("linux") || sample.includes("x11")) return "linux";
    return "unknown";
  }

  function applyRecommendation(os) {
    const activeOs = recommendationMap[os] ? os : "unknown";
    document.body.dataset.detectedOs = activeOs;

    const copy = recommendationMap[activeOs];
    const headline = document.getElementById("os-headline");
    const message = document.getElementById("os-message");
    if (headline) headline.textContent = copy.headline;
    if (message) message.textContent = copy.message;

    document.querySelectorAll("[data-os-target]").forEach((button) => {
      button.classList.toggle("is-recommended", button.getAttribute("data-os-target") === activeOs);
    });

    document.querySelectorAll("[data-os-card]").forEach((card) => {
      card.classList.toggle("is-recommended", card.getAttribute("data-os-card") === activeOs);
    });
  }

  applyRecommendation(detectOs());
})();