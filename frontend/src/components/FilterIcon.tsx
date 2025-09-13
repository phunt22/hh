import type { CSSProperties } from "react";
import styles from "./FilterIcon.module.css";

type FilterIconProps = {
  onClick: () => void;
  active?: boolean;
  style?: CSSProperties;
};

export default function FilterIcon({ onClick, active, style }: FilterIconProps) {
  return (
    <button
      onClick={onClick}
      aria-label="Filter events"
      className={`${styles.icon} ${active ? styles.active : ""}`}
      style={style}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square" style={{transition: 'color 0.15s ease'}}>
        <path d="M3 4h18M6 11h12M9 18h6" />
      </svg>
    </button>
  );
}


