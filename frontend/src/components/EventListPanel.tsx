import { useEffect, useRef, useState } from "react";
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
  const [isClosing, setIsClosing] = useState(false);
  const closeRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    // Ensure the close button is not focused on initial render
    const t = setTimeout(() => closeRef.current?.blur(), 0);
    return () => clearTimeout(t);
  }, []);

  const handleClose = () => {
    if (isClosing) return;
    setIsClosing(true);
    // Wait for CSS exit animation to finish before unmounting
    setTimeout(() => {
      onClose();
    }, 180);
  };

  return (
    <div
      className={`${styles.panel} ${isClosing ? styles.closing : ""}`}
      onWheelCapture={(e) => e.stopPropagation()}
      onTouchMoveCapture={(e) => e.stopPropagation()}
    >
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          {locationLabel || "Location"}
        </div>
        <button 
          ref={closeRef}
          onClick={handleClose} 
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
