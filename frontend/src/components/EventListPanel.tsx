import type { EventPoint } from "../types";
import styles from "./EventListPanel.module.css";
import EventCard from "./EventCard";

export type EventListPanelProps = {
  locationLabel: string;
  events: EventPoint[];
  onClose: () => void;
};

export default function EventListPanel({ locationLabel, events, onClose }: EventListPanelProps) {
  return (
    <div
      className={styles.panel}
      onWheelCapture={(e) => e.stopPropagation()}
      onTouchMoveCapture={(e) => e.stopPropagation()}
    >
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          {locationLabel || "Location"}
        </div>
        <button onClick={onClose} aria-label="Close" className={styles.closeBtn}>✕</button>
      </div>
      <div className={styles.listWrapper}>
        <div className={styles.list}>
          {events.map((e) => (
            <EventCard key={e.id} event={e} />
          ))}
          {events.length === 0 && (
            <div className={styles.empty}>No events at this location.</div>
          )}
        </div>
      </div>
    </div>
  );
}
