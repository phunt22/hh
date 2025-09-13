import type { EventPoint } from '../types';

// free with no key
export const DEFAULT_STYLE = "https://demotiles.maplibre.org/style.json";

// SF VIEW
export const DEFAULT_VIEW = { lon: -122.4194, lat: 37.7749, zoom: 11, bearing: 0, pitch: 0 };

// WORLD VIEW
export const WORLD_VIEW = { lon: 0, lat: 20, zoom: 1, bearing: 0, pitch: 0 };

// TODO replace with real data
export const SAMPLE_EVENTS: EventPoint[] = [
  { id: "1", title: "Union Sq",   lat: 37.7879, lng: -122.4074, popularity: 95 },
  { id: "2", title: "Market St",  lat: 37.7837, lng: -122.4089, popularity: 90 },
  { id: "3", title: "SoMa",       lat: 37.7786, lng: -122.4059, popularity: 85 },
  { id: "4", title: "Mission",    lat: 37.7599, lng: -122.4148, popularity: 75 },
  { id: "5", title: "North Beach", lat: 37.8040, lng: -122.4100, popularity: 70 }
];

export const CONTROL_BUTTON_STYLES: React.CSSProperties = {
  padding: "8px 12px",
  background: "#111",
  color: "#fff",
  border: "1px solid #333",
  borderRadius: 8,
  cursor: "pointer"
};
