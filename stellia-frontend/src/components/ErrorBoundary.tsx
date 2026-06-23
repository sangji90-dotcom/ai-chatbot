import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          position: "fixed", inset: 0, zIndex: 9999,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          background: "rgba(9,11,20,1)",
          gap: 20, padding: 32,
        }}>
          <div style={{ fontSize: 48 }}>✦</div>
          <div style={{
            fontSize: 24, fontWeight: 700,
            background: "var(--gradient-cosmic)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}>오류가 발생했어요</div>
          <div style={{ color: "var(--text-muted)", fontSize: 14, textAlign: "center", lineHeight: 1.7 }}>
            예기치 못한 오류가 발생했어요.<br />
            페이지를 새로고침하면 해결될 수 있어요.
          </div>
          {this.state.error && (
            <div style={{
              padding: "12px 20px", borderRadius: 12,
              background: "rgba(255,107,138,.08)",
              border: "1px solid rgba(255,107,138,.2)",
              color: "#ff6b8a", fontSize: 12, fontFamily: "monospace",
              maxWidth: 500, wordBreak: "break-all", textAlign: "center",
            }}>
              {this.state.error.message}
            </div>
          )}
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "14px 32px", borderRadius: 14, border: "none",
              background: "var(--gradient-cosmic)",
              color: "#fff", fontWeight: 700, fontSize: 15,
              cursor: "pointer",
              boxShadow: "0 0 30px rgba(139,124,255,.3)",
            }}
          >새로고침</button>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              padding: "10px 24px", borderRadius: 12,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)", fontSize: 14, cursor: "pointer",
            }}
          >다시 시도</button>
        </div>
      );
    }
    return this.props.children;
  }
}