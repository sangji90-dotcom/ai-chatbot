import { useState, useEffect, useCallback } from "react";

export interface ToastItem {
  id: string;
  message: string;
  type: "success" | "error" | "info" | "warning";
  duration?: number;
}

interface ToastProps {
  toasts: ToastItem[];
  onRemove: (id: string) => void;
}

export function Toast({ toasts, onRemove }: ToastProps) {
  useEffect(() => {
    toasts.forEach(toast => {
      const timer = setTimeout(() => onRemove(toast.id), toast.duration ?? 3000);
      return () => clearTimeout(timer);
    });
  }, [toasts]);

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
    success: "✓",
    error: "✕",
    info: "ℹ",
    warning: "⚠",
  };

  if (toasts.length === 0) return null;

  return (
    <div style={{
      position: "fixed", top: 20, left: "50%",
      transform: "translateX(-50%)",
      zIndex: 9999,
      display: "flex", flexDirection: "column", gap: 8,
      pointerEvents: "none",
    }}>
      {toasts.map(toast => (
        <div key={toast.id} style={{
          padding: "12px 20px", borderRadius: 14,
          background: COLOR[toast.type],
          border: `1px solid ${BORDER[toast.type]}`,
          color: TEXT[toast.type],
          fontSize: 14, fontWeight: 600,
          display: "flex", alignItems: "center", gap: 10,
          backdropFilter: "blur(20px)",
          boxShadow: "0 4px 20px rgba(0,0,0,.3)",
          pointerEvents: "auto",
          animation: "slideDown 0.3s ease",
          minWidth: 280, maxWidth: 400,
        }}>
          <span style={{ fontSize: 16 }}>{ICON[toast.type]}</span>
          <span style={{ flex: 1 }}>{toast.message}</span>
          <button onClick={() => onRemove(toast.id)} style={{
            background: "none", border: "none",
            color: TEXT[toast.type], cursor: "pointer", fontSize: 16, opacity: 0.7,
          }}>×</button>
        </div>
      ))}
      <style>{`
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

// 전역 토스트 훅
export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = useCallback((message: string, type: ToastItem["type"] = "info", duration = 3000) => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, message, type, duration }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const toast = {
    success: (msg: string) => addToast(msg, "success"),
    error: (msg: string) => addToast(msg, "error"),
    info: (msg: string) => addToast(msg, "info"),
    warning: (msg: string) => addToast(msg, "warning"),
  };

  return { toasts, removeToast, toast };
}