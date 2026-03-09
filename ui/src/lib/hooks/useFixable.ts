import { useState } from "react";

const STORAGE_KEY = "trivyal_fixable_only";

export function useFixable(defaultValue = false): [boolean, () => void] {
  const [fixable, setFixable] = useState<boolean>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored !== null ? stored === "true" : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  function toggle() {
    setFixable((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        // ignore storage errors
      }
      return next;
    });
  }

  return [fixable, toggle];
}
