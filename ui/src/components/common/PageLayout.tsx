import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Server,
  ShieldAlert,
  ListChecks,
  TrendingUp,
  History,
  LogOut,
  Sun,
  Moon,
  Menu,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { fetchDashboardSummary } from "@/lib/api/dashboard";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/priorities", icon: ListChecks, label: "Priorities" },
  { to: "/findings", icon: ShieldAlert, label: "Findings" },
  { to: "/agents", icon: Server, label: "Agents" },
  { to: "/insights", icon: TrendingUp, label: "Insights" },
  { to: "/scans", icon: History, label: "Scan History" },
];

function getInitialDark(): boolean {
  try {
    return localStorage.getItem("trivyal_theme") !== "light";
  } catch {
    return true;
  }
}

function NavContents({
  dark,
  toggleTheme,
  logout,
  onNavClick,
  priorityCount,
}: {
  dark: boolean;
  toggleTheme: () => void;
  logout: () => void;
  onNavClick?: () => void;
  priorityCount: number;
}) {
  return (
    <>
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            onClick={onNavClick}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium tracking-wide transition-colors",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
            {to === "/priorities" && priorityCount > 0 && (
              <span className="bg-primary/15 text-primary border-primary/30 ml-auto rounded-full border px-2 py-0.5 text-xs font-medium">
                {priorityCount}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="space-y-1 border-t p-2">
        <button
          onClick={toggleTheme}
          className="text-muted-foreground hover:bg-accent hover:text-accent-foreground flex w-full items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors"
        >
          {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          {dark ? "Light mode" : "Dark mode"}
        </button>
        <button
          onClick={logout}
          className="text-muted-foreground hover:bg-accent hover:text-accent-foreground flex w-full items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Log out
        </button>
      </div>
    </>
  );
}

export function PageLayout() {
  const logout = useAuthStore((s) => s.logout);
  const [dark, setDark] = useState(getInitialDark);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [priorityCount, setPriorityCount] = useState(0);

  useEffect(() => {
    fetchDashboardSummary()
      .then((s) => setPriorityCount(s.misconfig.total_active + s.fixable_cves))
      .catch(() => {});
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("trivyal_theme", next ? "dark" : "light");
    } catch {
      // ignore storage errors
    }
  }

  return (
    <div className="flex h-screen">
      {/* Desktop sidebar */}
      <aside className="bg-card hidden w-56 flex-col border-r lg:flex">
        <div className="flex h-14 items-center border-b px-4">
          <NavLink to="/" className="font-mono text-lg font-bold tracking-wide">
            trivy<span className="text-primary">al</span>
          </NavLink>
        </div>
        <NavContents
          dark={dark}
          toggleTheme={toggleTheme}
          logout={logout}
          priorityCount={priorityCount}
        />
      </aside>

      {/* Mobile top header */}
      <div className="flex flex-1 flex-col lg:contents">
        <header className="bg-card flex h-14 items-center justify-between border-b px-4 lg:hidden">
          <NavLink to="/" className="font-mono text-lg font-bold tracking-wide">
            trivy<span className="text-primary">al</span>
          </NavLink>
          <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                title="Open menu"
                className="h-10 w-10"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent>
              <SheetTitle className="sr-only">Navigation</SheetTitle>
              <div className="flex h-14 items-center border-b px-4">
                <NavLink
                  to="/"
                  className="font-mono text-lg font-bold tracking-wide"
                >
                  trivy<span className="text-primary">al</span>
                </NavLink>
              </div>
              <NavContents
                dark={dark}
                toggleTheme={toggleTheme}
                logout={logout}
                onNavClick={() => setSheetOpen(false)}
                priorityCount={priorityCount}
              />
            </SheetContent>
          </Sheet>
        </header>

        <main className="flex-1 overflow-x-hidden overflow-y-auto p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
