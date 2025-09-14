import { type CSSProperties } from "react";
import styles from "./TrendIcon.module.css";

type TrendIconProps = {
  onClick: () => void;
  disabled?: boolean;
  style?: CSSProperties;
  title?: string;
};

export default function TrendIcon({ onClick, disabled = false, style, title = "Show Busiest Cities" }: TrendIconProps) {
  return (
    <button 
      onClick={onClick} 
      disabled={disabled}
      aria-label="Show Busiest Cities" 
      title={title}
      className={styles.trendIcon}
      style={style}
    >
      <svg 
        width="18" 
        height="18" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      >
        <polyline points="22,12 18,12 15,21 9,3 6,9 2,9" />
      </svg>
    </button>
  );
}
