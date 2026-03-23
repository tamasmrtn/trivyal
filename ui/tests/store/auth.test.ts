import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "@/store/auth";

describe("auth store", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({ token: null });
  });

  it("initializes with null token when localStorage is empty", () => {
    expect(useAuthStore.getState().token).toBeNull();
  });

  it("setToken stores token in localStorage and updates state", () => {
    useAuthStore.getState().setToken("my-token");

    expect(useAuthStore.getState().token).toBe("my-token");
    expect(localStorage.getItem("trivyal_token")).toBe("my-token");
  });

  it("logout removes token from localStorage and clears state", () => {
    useAuthStore.getState().setToken("my-token");
    useAuthStore.getState().logout();

    expect(useAuthStore.getState().token).toBeNull();
    expect(localStorage.getItem("trivyal_token")).toBeNull();
  });
});
