import type { EventPoint } from '../types';
import { normalizeCategorySlug } from '../utils/categories';

const ATTENDANCE_CAP = 5000;

function computeHeatmapWeight(raw?: number | null): number {
  const value = typeof raw === 'number' && isFinite(raw) ? Math.max(raw, 0) : 0;
  const normalized = Math.log1p(value) / Math.log1p(ATTENDANCE_CAP);
  const clamped = Math.max(0, Math.min(1, normalized));
  const baseline = 0.03; // ensure non-zero contribution even for 0/missing
  return Math.max(baseline, clamped);
}

export const zoomToRadiusKm = (z: number) => {
  if (z >= 16) return 1.2;
  if (z >= 14) return 2.5;
  if (z >= 12) return 5;
  if (z >= 10) return 12;
  if (z >= 8)  return 30;
  if (z >= 6)  return 90;
  if (z >= 4)  return 250;
  return 1000;
};

export const toFeatureCollection = (rows: EventPoint[]) => ({
  type: "FeatureCollection" as const,
  features: rows.map((e) => ({
    type: "Feature" as const,
    geometry: { type: "Point" as const, coordinates: [e.lng, e.lat] },
    properties: {
      id: e.id,
      title: e.title,
      description: e.description ?? "",
      start: e.start ?? null,
      end: e.end ?? null,
      category: normalizeCategorySlug(e.category) || "",
      location: e.location ?? "",
      attendance: (e as any).attendance ?? (e as any).expectedAttendees ?? null,
      weight: computeHeatmapWeight((e as any).attendance ?? (e as any).expectedAttendees ?? null),
    }
  }))
});

// Simple debounce without external deps
export const debounce = <T extends (...args: any[]) => void>(fn: T, ms: number) => {
  let t: number | undefined;
  return (...args: Parameters<T>) => {
    if (t) window.clearTimeout(t);
    t = window.setTimeout(() => fn(...args), ms) as unknown as number;
  };
};

// find first symbol layer to insert beneath, keeps labels on top
export const findFirstSymbolLayerId = (map: any): string | null => {
  const layers = map.getStyle()?.layers ?? [];
  const symbol = layers.find((l: any) => l.type === "symbol");
  return symbol?.id ?? null;
};
