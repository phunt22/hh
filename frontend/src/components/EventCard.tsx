import type { EventPoint } from "../types";
import styles from "./EventCard.module.css";

export default function EventCard({ event }: { event: EventPoint }) {
  return (
    <div className={styles.card}>
      <div className={styles.title}>{event.title}</div>
      {(event.category || event.time) && (
        <div className={styles.subtitle}>
          {event.category ? event.category : null}
          {event.category && event.time ? " • " : null}
          {event.time ? new Date(event.time).toLocaleString() : null}
        </div>
      )}
      {typeof event.popularity === "number" && (
        <div className={styles.meta}>Popularity: {Math.round(event.popularity)}</div>
      )}
      {event.description && (
        <div className={styles.description}>
          {event.description.length > 200 ? event.description.slice(0, 197) + "…" : event.description}
        </div>
      )}
    </div>
  );
}
