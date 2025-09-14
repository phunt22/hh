import { useState } from "react";
import { formatCategoryLabel } from "../utils/categories";
import type { EventPoint } from "../types";
import styles from "./EventCard.module.css";

export default function EventCard({ event, onClick }: { event: EventPoint; onClick?: () => void }) {
  const [showSimilar, setShowSimilar] = useState(false);
  
  // i.e. "performing-arts" -> "Performing Arts"
  const prettifyCategory = (value?: string | null) => formatCategoryLabel(value || "");

  const formatDate = (iso?: string) => {
    if (!iso) return null;
    try {
      const date = new Date(iso);
      return date.toLocaleDateString() 
    } catch {
      return iso;
    }
  };

  const formatAttendees = (count?: number) => {
    if (count === undefined || count === null) return null; // should not happen, guard probably not neede
    if (count >= 1000) return `${Math.round(count / 1000)}K expected`;
    return `${count} expected`;
  };

  return (
    <div className={`${styles.card} ${onClick ? styles.clickable : ""}`} onClick={onClick} role={onClick ? "button" : undefined}>
      <div className={styles.title}>{event.title}</div>
      
      {(event.category || event.start || event.end) && (
        <div className={styles.subtitle}>
          {event.category && prettifyCategory(event.category)}
          {event.category && (event.start || event.end) ? " • " : null}
          {event.start && event.end
            ? (() => {
                const sd = new Date(event.start);
                const ed = new Date(event.end);
                const isMulti = sd.getFullYear() !== ed.getFullYear() || sd.getMonth() !== ed.getMonth() || sd.getDate() !== ed.getDate();
                return isMulti ? `${formatDate(event.start)} – ${formatDate(event.end)}` : formatDate(event.start);
              })()
            : (event.start ? formatDate(event.start) : null)}
        </div>
      )}
      
      {(event.attendance !== undefined && event.attendance !== null) && (
        <div className={styles.metaRow}>
          <span className={styles.meta}>{formatAttendees(event.attendance)}</span>
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
            onClick={(e) => { e.stopPropagation(); setShowSimilar(!showSimilar); }}
          >
            Similar Events ({event.similarEvents.length}) {showSimilar ? "▼" : "▶"}
          </button>
          {showSimilar && (
            <div className={styles.similarList}>
              {event.similarEvents.slice(0, 3).map((similar) => (
                <div key={similar.id} className={styles.similarItem}>
                  <div className={styles.similarTitle}>{similar.title}</div>
                  <div className={styles.similarMeta}>
                    {similar.category && <span>{prettifyCategory(similar.category)}</span>}
                    {similar.start && similar.end && (
                      <span>{(() => {
                        const sd = new Date(similar.start!);
                        const ed = new Date(similar.end!);
                        const isMulti = sd.getFullYear() !== ed.getFullYear() || sd.getMonth() !== ed.getMonth() || sd.getDate() !== ed.getDate();
                        return isMulti ? `${formatDate(similar.start)} – ${formatDate(similar.end)}` : formatDate(similar.start);
                      })()}</span>
                    )}
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
