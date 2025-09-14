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
        {/* Microphone icon for dictation/speech-to-text */}
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
        <line x1="12" y1="19" x2="12" y2="23" />
        <line x1="8" y1="23" x2="16" y2="23" />
      </svg>
    </button>
  );
}