import { useEffect } from "react";

type ToastProps = {
  message: string;
  duration?: number; // ms
  onClose?: () => void;
  style?: React.CSSProperties;
};

export default function Toast({ message, duration = 3000, onClose, style }: ToastProps) {
  useEffect(() => {
    const t = window.setTimeout(() => {
      onClose?.();
    }, duration) as unknown as number;
    return () => window.clearTimeout(t);
  }, [duration, onClose]);

  return (
    <div
      style={{
        position: "absolute",
        top: 12,
        left: "50%",
        transform: "translateX(-50%)",
        background: "rgba(20,20,20,0.92)",
        color: "#fff",
        padding: "10px 14px",
        borderRadius: 10,
        boxShadow: "0 6px 20px rgba(0,0,0,0.35)",
        fontSize: 14,
        zIndex: 2,
        pointerEvents: "none",
        ...style
      }}
    >
      {message}
    </div>
  );
}


