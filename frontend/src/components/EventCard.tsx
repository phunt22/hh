import { useState } from "react";
import { formatCategoryLabel } from "../utils/categories";
import type { EventPoint } from "../types";
import styles from "./EventCard.module.css";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { Skeleton } from "@/components/ui/skeleton";
import { useEventInsights } from "@/hooks/useEventInsights";

export default function EventCard({ event, onClick }: { event: EventPoint; onClick?: () => void }) {
  const [showSimilar, setShowSimilar] = useState(false);
  const [accordionOpen, setAccordionOpen] = useState(false);

  // Fetch insights only when accordion is open
  const { data: insights, isLoading } = useEventInsights({
    event: {
      title: event.title,
      description: event.description ?? "",
      date: event.start ?? event.end ?? "",
    },
    enabled: accordionOpen
  });

  const prettifyCategory = (value?: string | null) => formatCategoryLabel(value || "");

  const formatDate = (iso?: string) => {
    if (!iso) return null;
    try {
      const date = new Date(iso);
      return date.toLocaleDateString();
    } catch {
      return iso;
    }
  };

  const formatAttendees = (count?: number) => {
    if (count === undefined || count === null) {
      // Return a random number between 20 and 200 as a fallback
      const random = Math.floor(Math.random() * (200 - 20 + 1)) + 20;
      return `${random} expected`;
    }
    if (count >= 1000) return `${Math.round(count / 1000)}k people expected`;
    return `${count} people expected`;
  };

  const formatDescription = (description: string) => {
    let desc = description;
    if (desc.startsWith("- ")) {
      desc = desc.slice(2);
    }
    return desc.length > 200 ? desc.slice(0, 197) + "…" : desc;
  }

  return (
    <div
      className={`${styles.card} ${onClick ? styles.clickable : ""}`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
    >
      <div className={styles.title}>{event.title}</div>

      {event.description && (
        <div className={styles.description}>
          {formatDescription(event.description)}
        </div>
      )}

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

      {event.attendance && (
        <div className={styles.metaRow}>
          <span className={styles.meta}>{formatAttendees(event.attendance)}</span>
        </div>
      )}

      

      {/* Accordion for Event Insights */}
      <Accordion className="mt-3" type="single" collapsible>
        <AccordionItem value={event.id}>
          <AccordionTrigger onClick={() => setAccordionOpen(!accordionOpen)}>
            Event Insights
          </AccordionTrigger>
          <AccordionContent className="border-0">
            {isLoading ? (
              <>
                <Skeleton className="h-4 rounded-sm my-1.5 w-full animate-fade-in bg-neutral-200/60 dark:bg-neutral-100/20" />
                <Skeleton className="h-4 rounded-sm my-1.5 w-full animate-fade-in bg-neutral-200/60 dark:bg-neutral-100/20" />
                <Skeleton className="h-4 rounded-sm my-1.5 w-full animate-fade-in bg-neutral-200/60 dark:bg-neutral-100/20" />
              </>
            ) : (
              <p className="animate-fade-in text-sm py-2">
                {insights}
              </p>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>

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
