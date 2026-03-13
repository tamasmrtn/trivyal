import { render, screen } from "@testing-library/react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

function renderDialog(children?: React.ReactNode) {
  return render(
    <Dialog open={true}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Test</DialogTitle>
        </DialogHeader>
        {children}
      </DialogContent>
    </Dialog>,
  );
}

describe("DialogContent mobile usability", () => {
  it("has max-height class to prevent overflow on short screens", () => {
    renderDialog();
    const dialog = screen.getByRole("dialog");
    expect(dialog.className).toMatch(/max-h-/);
  });

  it("has overflow-y-auto so tall content is scrollable", () => {
    renderDialog();
    const dialog = screen.getByRole("dialog");
    expect(dialog.className).toContain("overflow-y-auto");
  });
});

describe("DialogFooter mobile usability", () => {
  it("has gap-2 so stacked mobile buttons have spacing between them", () => {
    const { container } = render(
      <DialogFooter>
        <button>Cancel</button>
        <button>Confirm</button>
      </DialogFooter>,
    );
    const footer = container.firstChild as HTMLElement;
    expect(footer.className).toContain("gap-2");
  });
});
