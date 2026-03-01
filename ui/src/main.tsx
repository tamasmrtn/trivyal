import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import { PageLayout } from "@/components/common/PageLayout";
import { Dashboard } from "@/pages/Dashboard";
import { Login } from "@/pages/Login";
import "./app.css";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <RequireAuth>
            <PageLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
      </Route>
    </Routes>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
