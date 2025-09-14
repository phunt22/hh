import { useEffect, useRef } from "react";
import styles from "./FilterOverlay.module.css";
import { formatCategoryLabel } from "../utils/categories";
import { getCategoryColor, getReadableTextColor } from "../constants/categoryColors";

type FilterOverlayProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedCategories: string[]; // normalized
  onToggleCategory: (slug: string) => void;
  onSelectAll: () => void;
  onClearAll: () => void;
  categories?: string[]; // normalized list from API
};

export default function FilterOverlay({
  isOpen,
  onClose,
  selectedCategories,
  onToggleCategory,
  onSelectAll,
  onClearAll,
  categories,
}: FilterOverlayProps) {
  const closeRef = useRef<HTMLButtonElement | null>(null);
  // ensure close button not focused initially on open
  useEffect(() => {
    if (isOpen) {
      const t = setTimeout(() => closeRef.current?.blur(), 0);
      return () => clearTimeout(t);
    }
  }, [isOpen]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.addEventListener("keydown", onKey);
      return () => document.removeEventListener("keydown", onKey);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className={styles.backdrop} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.container} role="dialog" aria-modal="true" aria-label="Filter events by category">
        <div className={styles.header}>
          <div className={styles.title}>Filter by Category</div>
          <button className={styles.closeButton} onClick={onClose} aria-label="Close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className={styles.grid}>
          {(categories ?? []).map((slug) => {
            const isChecked = selectedCategories.includes(slug);
            const color = getCategoryColor(slug);
            const textColor = getReadableTextColor(color);
            const checkboxStyle = isChecked
              ? { backgroundColor: color, borderColor: color, color: textColor }
              : { borderColor: color };
            return (
              <button
                key={slug}
                className={styles.item}
                onClick={() => onToggleCategory(slug)}
                aria-pressed={isChecked}
              >
                <span
                  className={`${styles.checkbox} ${isChecked ? styles.checkboxChecked : ""}`}
                  aria-hidden
                  style={checkboxStyle}
                  title={formatCategoryLabel(slug)}
                >
                  {isChecked ? "✓" : ""}
                </span>
                <span>{formatCategoryLabel(slug)}</span>
              </button>
            );
          })}
        </div>

        <div className={styles.footer}>
          <div>{selectedCategories.length === 0 && "Showing all events"}</div>
          <div className={styles.inlineButtons}>
            <button className={styles.button} onClick={onSelectAll}>Select All</button>
            <button className={styles.button} onClick={onClearAll}>Clear</button>
            <button className={styles.doneButton} onClick={onClose}>Filter</button>
          </div>
        </div>
      </div>
    </div>
  );
}


