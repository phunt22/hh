import { useState } from "react";
import type { EventPoint } from "../types";
import styles from "./EventCard.module.css";

export default function EventCard({ event }: { event: EventPoint }) {
  const [showSimilar, setShowSimilar] = useState(false);
  
  const formatDate = (timeStr?: string) => {
    if (!timeStr) return null;
    try {
      const date = new Date(timeStr);
      return date.toLocaleDateString() + " at " + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return timeStr;
    }
  };

  const formatAttendees = (count?: number) => {
    if (!count) return null;
    if (count >= 1000) return `${Math.round(count / 1000)}K expected`;
    return `${count} expected`;
  };

  return (
    <div className={styles.card}>
      <div className={styles.title}>{event.title}</div>
      
      {(event.category || event.time) && (
        <div className={styles.subtitle}>
          {event.category ? event.category : null}
          {event.category && event.time ? " • " : null}
          {event.time ? formatDate(event.time) : null}
        </div>
      )}
      
      {event.expectedAttendees && (
        <div className={styles.metaRow}>
          <span className={styles.meta}>{formatAttendees(event.expectedAttendees)}</span>
        </div>
      )}
      
      {event.description && (
        <div className={styles.description}>
          {event.description.length > 200 ? event.description.slice(0, 197) + "…" : event.description}
        </div>
      )}
      
      {event.similarEvents && event.similarEvents.length > 0 && (
        <div className={styles.similarSection}>
          <button 
            className={styles.similarToggle}
            onClick={() => setShowSimilar(!showSimilar)}
          >
            Similar Events ({event.similarEvents.length}) {showSimilar ? "▼" : "▶"}
          </button>
          {showSimilar && (
            <div className={styles.similarList}>
              {event.similarEvents.slice(0, 3).map((similar) => (
                <div key={similar.id} className={styles.similarItem}>
                  <div className={styles.similarTitle}>{similar.title}</div>
                  <div className={styles.similarMeta}>
                    {similar.category && <span>{similar.category}</span>}
                    {similar.time && <span>{formatDate(similar.time)}</span>}
                  </div>
                </div>
              ))}
              {event.similarEvents.length > 3 && (
                <div className={styles.similarMore}>
                  +{event.similarEvents.length - 3} more
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
