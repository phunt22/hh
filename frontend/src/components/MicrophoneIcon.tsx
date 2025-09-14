import { type CSSProperties } from "react";
import styles from "./MicrophoneIcon.module.css";

type MicrophoneIconProps = {
  onClick: () => void;
  disabled?: boolean;
  isRecording?: boolean;
  style?: CSSProperties;
  title?: string;
};

export default function MicrophoneIcon({ 
  onClick, 
  disabled = false, 
  isRecording = false, 
  style, 
  title = "Record Voice Message" 
}: MicrophoneIconProps) {
  return (
    <button 
      onClick={onClick} 
      disabled={disabled}
      aria-label="Record Voice Message" 
      title={title}
      className={`${styles.microphoneIcon} ${isRecording ? styles.recording : ''}`}
      style={style}
    >
      <svg 
        width="18" 
        height="18" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="2.5" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      >
        {/* Audio waveform bars like the one in the image */}
        <line x1="3" y1="12" x2="3" y2="12" />
        <line x1="6" y1="8" x2="6" y2="16" />
        <line x1="9" y1="4" x2="9" y2="20" />
        <line x1="12" y1="6" x2="12" y2="18" />
        <line x1="15" y1="2" x2="15" y2="22" />
        <line x1="18" y1="9" x2="18" y2="15" />
        <line x1="21" y1="10" x2="21" y2="14" />
      </svg>
    </button>
  );
}