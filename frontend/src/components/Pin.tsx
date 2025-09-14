import type { Map as MLMap } from "maplibre-gl";
import { getCategoryColor } from "../constants/categoryColors";

type PinProps = {
  color?: string;
  size?: number;
  style?: React.CSSProperties;
  useEmoji?: boolean;
};

export default function Pin({ color = "#FF3B3B", size = 32, style, useEmoji = false }: PinProps) {
  if (useEmoji) {
    return (
      <div style={{ fontSize: size * 0.8, lineHeight: 1, ...style }}>
        📍
      </div>
    );
  }

  return (
    <svg width={size} height={size} viewBox="0 0 64 64" style={style} xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <ellipse cx="32" cy="52" rx="4" ry="1.5" fill="#000" opacity="0.12" />
      <rect x="31.4" y="26" width="5" height="18" rx="0.6" fill="#64748B" />
      <circle cx="32" cy="18" r="8" fill={color} stroke="rgba(255,255,255,0.5)" strokeWidth="0.5" />
    </svg>
  );
}

export function buildEmojiPinSvg(color: string, px: number): string {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${px}" height="${px}" viewBox="0 0 64 64">
  <ellipse cx="32" cy="52" rx="4" ry="1.5" fill="#000000" opacity="0.12" />
  <rect x="31.4" y="26" width="1.2" height="18" rx="0.6" fill="#64748B" />
  <circle cx="32" cy="18" r="8" fill="${color}" stroke="rgba(255,255,255,0.5)" stroke-width="0.5" />
</svg>`;
}

export async function addPinImageToMap(map: MLMap, id: string, color: string, size = 128): Promise<void> {
  const svg = buildEmojiPinSvg(color, size);
  const url = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  await rasterizeSvgToMapImage(map, id, url, size);
}

export function ensureCategoryPins(map: MLMap, sourceId = "events") {
  try {
    const features = map.querySourceFeatures(sourceId) || [];
    const seen = new Set<string>();
    for (const f of features) {
      const slug = String(f.properties?.category || "");
      if (!slug || seen.has(slug)) continue;
      seen.add(slug);
      const id = `pin-${slug}`;
      if ((map as any).hasImage && (map as any).hasImage(id)) continue;
      const color = getCategoryColor(slug);
      addPinImageToMap(map, id, color).catch(() => {});
    }
  } catch {
    // ignore
  }
}

function rasterizeSvgToMapImage(map: MLMap, id: string, url: string, size: number): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        try {
          const canvas = document.createElement("canvas");
          canvas.width = size;
          canvas.height = size;
          const ctx = canvas.getContext("2d");
          if (!ctx) return reject(new Error("2d ctx unavailable"));
          ctx.clearRect(0, 0, size, size);
          ctx.drawImage(img, 0, 0, size, size);
          const imageData = ctx.getImageData(0, 0, size, size);
          (map as any).addImage(id, imageData, { pixelRatio: 2 });
          resolve();
        } catch (err) {
          reject(err);
        }
      };
      img.onerror = () => reject(new Error("Failed to load SVG"));
      img.src = url;
    } catch (e) {
      reject(e);
    }
  });
}
