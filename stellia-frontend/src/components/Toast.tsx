import { useState, useEffect, useCallback, createContext, useContext, type ReactNode } from "react";

export interface ToastItem {
  id: string;
  message: string;
  type: "success" | "error" | "info" | "warning";
  duration?: number;
}

// Context
const ToastContext = createContext<{
  toast: {
    success: (msg: string) => void;
    error: (msg: string) => void;
    info: (msg: string) => void;
    warning: (msg: string) => void;
  }
} | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx.toast;
}

// Provider
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = useCallback((message: string, type: ToastItem["type"] = "info", duration = 3000) => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, message, type, duration }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
  }, []);

  const toast = {
    success: (msg: string) => addToast(msg, "success"),
    error: (msg: string) => addToast(msg, "error"),
    info: (msg: string) => addToast(msg, "info"),
    warning: (msg: string) => addToast(msg, "warning"),
  };

  const COLOR: Record<string, string> = {
    success: "rgba(73,216,154,.15)",
    error: "rgba(255,107,138,.15)",
    info: "rgba(139,124,255,.15)",
    warning: "rgba(255,200,80,.15)",
  };
  const BORDER: Record<string, string> = {
    success: "rgba(73,216,154,.3)",
    error: "rgba(255,107,138,.3)",
    info: "rgba(139,124,255,.3)",
    warning: "rgba(255,200,80,.3)",
  };
  const TEXT: Record<string, string> = {
    success: "#49d89a",
    error: "#ff6b8a",
    info: "var(--primary)",
    warning: "#ffc850",
  };
  const ICON: Record<string, string> = {
    success: "✓", error: "✕", info: "ℹ", warning: "⚠",
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {toasts.length > 0 && (
        <div style={{
          position: "fixed", top: 20, left: "50%",
          transform: "translateX(-50%)",
          zIndex: 9999,
          display: "flex", flexDirection: "column", gap: 8,
          pointerEvents: "none",
        }}>
          {toasts.map(t => (
            <div key={t.id} style={{
              padding: "12px 20px", borderRadius: 14,
              background: COLOR[t.type],
              border: `1px solid ${BORDER[t.type]}`,
              color: TEXT[t.type],
              fontSize: 14, fontWeight: 600,
              display: "flex", alignItems: "center", gap: 10,
              backdropFilter: "blur(20px)",
              boxShadow: "0 4px 20px rgba(0,0,0,.3)",
              minWidth: 280, maxWidth: 400,
              animation: "slideDown 0.3s ease",
            }}>
              <span style={{ fontSize: 16 }}>{ICON[t.type]}</span>
              <span style={{ flex: 1 }}>{t.message}</span>
            </div>
          ))}
          <style>{`
            @keyframes slideDown {
              from { opacity: 0; transform: translateY(-10px); }
              to { opacity: 1; transform: translateY(0); }
            }
          `}</style>
        </div>
      )}
    </ToastContext.Provider>
  );
}