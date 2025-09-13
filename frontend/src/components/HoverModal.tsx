import styles from "./HoverModal.module.css";

export type HoverInfo = {
  x: number;
  y: number;
  properties: {
    id: string;
    title: string;
    description?: string;
    start?: string;
    end?: string;
    category?: string;
    attendance?: number;
  };
} | null;

export default function HoverModal({ info }: { info: HoverInfo }) {
  if (!info) return null;

  const { x, y, properties } = info;
  const { title, description, start, end, category, attendance } = properties;

  const prettifyCategory = (value?: string | null) => {
    if (!value) return "";
    return value
      .replace(/[-_]+/g, " ")
      .trim()
      .split(/\s+/)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(" ");
  };

  const formatDateOrRange = (s?: string, e?: string) => {
    if (s && e) {
      const sd = new Date(s);
      const ed = new Date(e);
      const isMulti = sd.getFullYear() !== ed.getFullYear() || sd.getMonth() !== ed.getMonth() || sd.getDate() !== ed.getDate();
      return isMulti ? `${sd.toLocaleDateString()} – ${ed.toLocaleDateString()}` : sd.toLocaleDateString();
    }
    if (s) return new Date(s).toLocaleDateString();
    if (e) return new Date(e).toLocaleDateString();
    return null;
  };

  return (
    <div
      className={styles.card}
      style={{ left: x + 12, top: y + 12 }}
      onWheelCapture={(e) => e.stopPropagation()}
      onTouchMoveCapture={(e) => e.stopPropagation()}
    >
      <div className={styles.title}>{title || "Event"}</div>
      {(category || start || end) && (
        <div className={styles.subtitle}>
          {category ? prettifyCategory(category) : null}
          {category && (start || end) ? " • " : null}
          {formatDateOrRange(start, end)}
        </div>
      )}
      {typeof attendance === "number" && !Number.isNaN(attendance) && (
        <div className={styles.meta}>
          {attendance >= 1000 ? `${Math.round(attendance / 1000)}K expected` : `${attendance} expected`}
        </div>
      )}
      {description && (
        <div className={styles.description}>
          {description.length > 160 ? description.slice(0, 157) + "…" : description}
        </div>
      )}
    </div>
  );
}
