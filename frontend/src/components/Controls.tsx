import type { CSSProperties } from "react";
import { CONTROL_BUTTON_STYLES } from '../constants/mapConstants';

type ControlsProps = {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
  style?: CSSProperties;
};

export default function Controls({ onZoomIn, onZoomOut, onReset, style }: ControlsProps) {
  return (
    <div style={{ position: "absolute", right: 12, bottom: 12, display: "flex", gap: 8, ...style }}>
      <button onClick={onZoomIn} style={CONTROL_BUTTON_STYLES}>+</button>
      <button onClick={onZoomOut} style={CONTROL_BUTTON_STYLES}>−</button>
      <button onClick={onReset} style={CONTROL_BUTTON_STYLES}>Reset</button>
    </div>
  );
}


