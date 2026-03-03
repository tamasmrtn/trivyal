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
} from "lucide-react";
import { useState } from "react";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";

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

export function PageLayout() {
  const logout = useAuthStore((s) => s.logout);
  const [dark, setDark] = useState(getInitialDark);

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
      <aside className="bg-card flex w-56 flex-col border-r">
        <div className="flex h-14 items-center border-b px-4">
          <span className="font-mono text-lg font-bold tracking-wide">
            trivy<span className="text-primary">al</span>
          </span>
        </div>
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
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
      </aside>
      <main className="flex-1 overflow-auto p-8">
        <Outlet />
      </main>
    </div>
  );
}
