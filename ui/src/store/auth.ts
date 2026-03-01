import { create } from "zustand";

interface AuthState {
  token: string | null;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("trivyal_token"),
  setToken: (token) => {
    localStorage.setItem("trivyal_token", token);
    set({ token });
  },
  logout: () => {
    localStorage.removeItem("trivyal_token");
    set({ token: null });
  },
}));
