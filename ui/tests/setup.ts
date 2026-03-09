import "@testing-library/jest-dom";

// recharts ResponsiveContainer uses ResizeObserver which jsdom doesn't provide
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// jsdom 26.x removed in-memory localStorage — provide a simple mock
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();
Object.defineProperty(global, "localStorage", {
  value: localStorageMock,
  writable: true,
});

// Clear localStorage before each test so fixable/auth state doesn't bleed between tests
beforeEach(() => {
  localStorage.clear();
});
