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
      className="absolute top-3 left-1/2 transform -translate-x-1/2 bg-gray-800/90 text-white px-3.5 py-2.5 rounded-lg shadow-lg text-sm z-10 pointer-events-none"
      style={style}
    >
      {message}
    </div>
  );
}


