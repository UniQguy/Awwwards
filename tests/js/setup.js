// Setup file for Vitest jsdom environment
if (typeof window !== "undefined") {
  window.matchMedia = window.matchMedia || function (query) {
    return {
      matches: false,
      media: query,
      onchange: null,
      addListener: function () {},
      removeListener: function () {},
      addEventListener: function () {},
      removeEventListener: function () {},
      dispatchEvent: function () {
        return true;
      },
    };
  };
}
