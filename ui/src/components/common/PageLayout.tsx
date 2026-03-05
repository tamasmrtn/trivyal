import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Server,
  ShieldAlert,
  TrendingUp,
  History,
  Settings,
  LogOut,
  Sun,
  Moon,
  Menu,
} from "lucide-react";
import { useState } from "react";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/agents", icon: Server, label: "Agents" },
  { to: "/findings", icon: ShieldAlert, label: "Findings" },
  { to: "/insights", icon: TrendingUp, label: "Insights" },
  { to: "/scans", icon: History, label: "Scan History" },
  { to: "/settings", icon: Settings, label: "Settings" },
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
}: {
  dark: boolean;
  toggleTheme: () => void;
  logout: () => void;
  onNavClick?: () => void;
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
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium tracking-wide transition-colors",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="space-y-1 border-t p-2">
        <button
          onClick={toggleTheme}
          className="text-muted-foreground hover:bg-accent hover:text-accent-foreground flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
        >
          {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          {dark ? "Light mode" : "Dark mode"}
        </button>
        <button
          onClick={logout}
          className="text-muted-foreground hover:bg-accent hover:text-accent-foreground flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
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
      <aside className="bg-card hidden w-56 flex-col border-r sm:flex">
        <div className="flex h-14 items-center border-b px-4">
          <span className="font-mono text-lg font-bold tracking-wide">
            trivy<span className="text-primary">al</span>
          </span>
        </div>
        <NavContents dark={dark} toggleTheme={toggleTheme} logout={logout} />
      </aside>

      {/* Mobile top header */}
      <div className="flex flex-1 flex-col sm:contents">
        <header className="bg-card flex h-14 items-center justify-between border-b px-4 sm:hidden">
          <span className="font-mono text-lg font-bold tracking-wide">
            trivy<span className="text-primary">al</span>
          </span>
          <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" title="Open menu">
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent>
              <div className="flex h-14 items-center border-b px-4">
                <span className="font-mono text-lg font-bold tracking-wide">
                  trivy<span className="text-primary">al</span>
                </span>
              </div>
              <NavContents
                dark={dark}
                toggleTheme={toggleTheme}
                logout={logout}
                onNavClick={() => setSheetOpen(false)}
              />
            </SheetContent>
          </Sheet>
        </header>

        <main className="flex-1 overflow-auto p-4 sm:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
