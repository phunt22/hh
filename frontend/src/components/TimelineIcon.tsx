import type { CSSProperties } from "react";
import styles from "./FilterIcon.module.css";

type FilterIconProps = {
  onClick: () => void;
  active?: boolean;
  style?: CSSProperties;
};

export default function TimelineIcon({ onClick, active, style }: FilterIconProps) {
  return (
    <button
      onClick={onClick}
      aria-label="Play Timeline"
      className={`${styles.icon} ${active ? styles.active : ""}`}
      style={style}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style={{ transition: 'color 0.15s ease' }}>
        {active ? (
            <rect x="6" y="6" width="12" height="12" />
            ) : (
            <polygon points="6,4 20,12 6,20" />)}
      </svg>
    </button>
  );
}
