import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Login } from "@/pages/Login";

vi.mock("@/lib/api/auth", () => ({
  login: vi.fn(),
}));

vi.mock("@/store/auth", () => ({
  useAuthStore: vi.fn((selector: (s: { setToken: () => void }) => unknown) =>
    selector({ setToken: vi.fn() }),
  ),
}));

function renderLogin() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>,
  );
}

describe("Login", () => {
  it("renders username and password inputs", () => {
    renderLogin();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("inputs have h-11 for adequate touch target height", () => {
    renderLogin();
    const usernameInput = screen.getByLabelText("Username");
    const passwordInput = screen.getByLabelText("Password");
    expect(usernameInput.className).toContain("h-11");
    expect(passwordInput.className).toContain("h-11");
  });

  it("submit button has h-11 for adequate touch target height", () => {
    renderLogin();
    const submitBtn = screen.getByRole("button", { name: /sign in/i });
    expect(submitBtn.className).toContain("h-11");
  });

  it("outer container has px-4 to prevent card from touching screen edges", () => {
    const { container } = renderLogin();
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv.className).toContain("px-4");
  });
});
