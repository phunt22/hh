import { type CSSProperties } from "react";
import styles from "./SpeakerIcon.module.css";

type SpeakerIconProps = {
  onClick: () => void;
  disabled?: boolean;
  isDictating?: boolean;
  style?: CSSProperties;
  title?: string;
};

export default function SpeakerIcon({ 
  onClick, 
  disabled = false, 
  isDictating = false, 
  style, 
  title = "Type as You Speak" 
}: SpeakerIconProps) {
  return (
    <button 
      onClick={onClick} 
      disabled={disabled}
      aria-label="Type as You Speak" 
      title={title}
      className={`${styles.speakerIcon} ${isDictating ? styles.dictating : ''}`}
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
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    </button>
  );
}
