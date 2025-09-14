export const CATEGORY_COLORS: Record<string, string> = {
  // Knowledge & civic
  "academic": "#3B82F6",           // blue-500 (distinct blue)
  "politics": "#EF4444",           // red-500 (bright red)

  // Holidays & observances
  "public-holidays": "#F59E0B",    // amber-500 (festive gold)
  "school-holidays": "#FDE047",    // yellow-300 (brighter yellow)
  "observances": "#8B5CF6",        // violet-500
  "daylight-savings": "#65A30D",   // lime-600 (deeper lime)

  // Events & culture
  "conferences": "#0EA5E9",        // sky-500
  "expos": "#06B6D4",              // cyan-500
  "concerts": "#EC4899",           // pink-500 (distinct from red)
  "festivals": "#FB923C",          // orange-400 (brighter orange)
  "performing-arts": "#A855F7",    // purple-500
  "community": "#10B981",          // emerald-500 (distinct green)

  // Sports
  "sports": "#22C55E",             // green-500

  // Disruption & alerts
  "airport-delays": "#64748B",     // slate-500
  "severe-weather": "#EA580C",     // orange-600 (alert)
  "disasters": "#B91C1C",          // red-600 (distinct from politics)
  "health-warnings": "#D946EF"     // fuchsia-500 (distinct magenta)
};

const DEFAULT_CATEGORY_COLOR = "#6B7280"; // neutral gray fallback

export function getCategoryColor(slug: string | null | undefined): string {
  if (!slug) return DEFAULT_CATEGORY_COLOR;
  const key = slug.toLowerCase();
  return CATEGORY_COLORS[key] ?? DEFAULT_CATEGORY_COLOR;
}

// Simple YIQ-based contrast to ensure readable checkmark on colored background
export function getReadableTextColor(hexColor: string): string {
  const hex = hexColor.replace("#", "");
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const yiq = (r * 299 + g * 587 + b * 114) / 1000;
  return yiq >= 160 ? "#000000" : "#FFFFFF";
}


