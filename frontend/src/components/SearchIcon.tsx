import { type CSSProperties } from "react";
import styles from "./SearchIcon.module.css";

type SearchIconProps = {
  onClick: () => void;
  style?: CSSProperties;
};

export default function SearchIcon({ onClick, style }: SearchIconProps) {

  return (
    <button 
      onClick={onClick} 
      aria-label="Search" 
      className={styles.searchIcon}
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
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
    </button>
  );
}
