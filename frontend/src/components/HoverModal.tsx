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
    expectedAttendees?: number;
  };
} | null;

export default function HoverModal({ info }: { info: HoverInfo }) {
  if (!info) return null;

  const { x, y, properties } = info;
  const { title, description, time, category, expectedAttendees } = properties;

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
      {typeof expectedAttendees === "number" && !Number.isNaN(expectedAttendees) && (
        <div className={styles.meta}>
          {expectedAttendees >= 1000 ? `${Math.round(expectedAttendees / 1000)}K expected` : `${expectedAttendees} expected`}
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
