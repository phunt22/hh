export type EventPoint = {
  id: string;
  title: string;
  lat: number;
  lng: number;
  description?: string;
  popularity?: number; // [0,100]
  time?: string; // ISO 8601
  category?: string;
  location?: string;
};

export type GlobeProps = {
  data?: EventPoint[];

  /**
   * Optional async fetcher. When the camera settles, we call this with the
   * current center and a zoom-based radiusKm; return events to render.
   */
  onViewportQuery?: (
    center: { lat: number; lng: number },
    radiusKm: number,
    view: { zoom: number; bearing: number; pitch: number }
  ) => Promise<EventPoint[]>;

  mapStyle?: string;

  initialView?: { lon: number; lat: number; zoom: number; bearing?: number; pitch?: number };

  /** Max points to keep client-side (safety cap) */
  maxClientPoints?: number;

  /** Debounce for viewport fetches (ms) */
  fetchDebounceMs?: number;

  /** If true, shows simple zoom, in, reset */
  showControls?: boolean;

  /** Inline style for the container (defaults to full screen). */
  style?: React.CSSProperties;

  /** If true, attempts to center map at user's geolocation on load. */
  startAtUserLocation?: boolean;
};

export type MapViewport = {
  center: { lat: number; lng: number };
  radiusKm: number;
  view: { zoom: number; bearing: number; pitch: number };
};
