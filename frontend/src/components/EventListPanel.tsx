import type { EventPoint } from "../types";
import styles from "./EventListPanel.module.css";
import EventCard from "./EventCard";

export type EventListPanelProps = {
  locationLabel: string;
  events: EventPoint[];
  onClose: () => void;
  onEventClick?: (e: EventPoint) => void;
  isSearchResults: boolean;
};

export default function EventListPanel({ locationLabel, events, onClose, onEventClick, isSearchResults }: EventListPanelProps) {
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
        <button 
          onClick={onClose} 
          aria-label="Close" 
          className={`${styles.closeBtn} ${isSearchResults ? styles.closeBtnDanger : ""}`}
          title={isSearchResults ? "Clear search results" : "Close"}
        >✕</button>
      </div>
      <div className={styles.listWrapper}>
        <div className={styles.list}>
          {events.map((e) => (
            <div key={e.id} onClick={() => onEventClick?.(e)}>
              <EventCard event={e} onClick={() => onEventClick?.(e)} />
            </div>
          ))}
          {events.length === 0 && (
            <div className={styles.empty}>No events at this location.</div>
          )}
        </div>
      </div>
    </div>
  );
}
