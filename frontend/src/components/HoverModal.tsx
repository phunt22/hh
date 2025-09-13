import styles from "./HoverModal.module.css";

export type HoverInfo = {
  x: number;
  y: number;
  properties: {
    id: string;
    title: string;
    description?: string;
    time?: string;
    category?: string;
    popularity?: number;
  };
} | null;

export default function HoverModal({ info }: { info: HoverInfo }) {
  if (!info) return null;

  const { x, y, properties } = info;
  const { title, description, time, category, popularity } = properties;

  return (
    <div
      className={styles.card}
      style={{ left: x + 12, top: y + 12 }}
      onWheelCapture={(e) => e.stopPropagation()}
      onTouchMoveCapture={(e) => e.stopPropagation()}
    >
      <div className={styles.title}>{title || "Event"}</div>
      {(category || time) && (
        <div className={styles.subtitle}>
          {category ? category : null}
          {category && time ? " • " : null}
          {time ? new Date(time).toLocaleString() : null}
        </div>
      )}
      {typeof popularity === "number" && !Number.isNaN(popularity) && (
        <div className={styles.meta}>Popularity: {Math.round(popularity)}</div>
      )}
      {description && (
        <div className={styles.description}>
          {description.length > 160 ? description.slice(0, 157) + "…" : description}
        </div>
      )}
    </div>
  );
}
