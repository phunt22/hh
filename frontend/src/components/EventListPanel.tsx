import type { EventPoint } from "../types";
import styles from "./EventListPanel.module.css";
import EventCard from "./EventCard";
import { useEffect, useRef, useState } from "react";

export type EventListPanelProps = {
  locationLabel: string;
  events: EventPoint[];
  onClose: () => void;
  onEventClick?: (e: EventPoint) => void;
  isSearchResults: boolean;
  onClosingChange?: (closing: boolean) => void;
  header?: React.ReactNode;
};

export default function EventListPanel({ header,locationLabel, events, onClose, onEventClick, isSearchResults, onClosingChange }: EventListPanelProps) {
  const [isClosing, setIsClosing] = useState(false);
  const closeRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    const t = setTimeout(() => closeRef.current?.blur(), 0);
    return () => clearTimeout(t);
  }, []);

  // Sort events by expected attendance (descending)
  const sortedByAttendance = (events || []).slice().sort((a, b) => {
    const aAttendance = a.attendance ?? 0;
    const bAttendance = b.attendance ?? 0;
    return bAttendance - aAttendance;
  });

  const handleClose = () => {
    if (isClosing) return;
    setIsClosing(true);
    onClosingChange?.(true);

    setTimeout(() => {
      onClose();
      onClosingChange?.(false);
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
          className={styles.closeBtn}
          title={isSearchResults ? "Clear search results" : "Close"}
        >✕</button>
      </div>

      <div className={styles.listWrapper}>
        <div className={styles.list}>
          {header && (
            <div>
              {header}
            </div>
          )}
          {sortedByAttendance.slice(0, 10).map((e) => (
            <div key={e.id} onClick={() => onEventClick?.(e)}>
              <EventCard event={e} onClick={() => onEventClick?.(e)} />
            </div>
          ))}
          {sortedByAttendance.length === 0 && (
            <div className={styles.empty}>No events at this location.</div>
          )}
        </div>
      </div>
    </div>
  );
}
