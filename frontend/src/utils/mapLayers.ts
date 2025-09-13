import type { Map as MLMap } from "maplibre-gl";
import { findFirstSymbolLayerId } from './mapUtils';

export function setupMapLayers(map: MLMap) {
	setupHeatmapLayer(map);
	setupPinLayer(map);
}

function setupHeatmapLayer(map: MLMap) {
	if (!map.getLayer("events-heat")) {
		map.addLayer(
			{
				id: "events-heat",
				type: "heatmap",
				source: "events",
				maxzoom: 18,
				paint: {
					// weight: use expectedAttendees (0..5000 -> 0..1)
					"heatmap-weight": [
						"interpolate",
						["linear"],
						["coalesce", ["to-number", ["get", "expectedAttendees"]], 0],
						0, 0,
						5000, 1
					],

					// intensity grows with zoom => crisper red cores when zoomed
					"heatmap-intensity": [
						"interpolate",
						["linear"],
						["zoom"],
						0, 0.6,
						9, 1.2,
						13, 1.8
					],

					// radius in pixels by zoom (tuned for city detail)
					"heatmap-radius": [
						"interpolate",
						["linear"],
						["zoom"],
						0, 2,
						7, 18,
						10, 28,
						13, 42,
						16, 64
					],

					// classic blue→cyan→yellow→orange→red
					"heatmap-color": [
						"interpolate",
						["linear"],
						["heatmap-density"],
						0.0, "rgba(0, 0, 255, 0.0)",
						0.15, "rgba(0, 180, 255, 0.6)",
						0.35, "rgba(0, 255, 150, 0.8)",
						0.55, "rgba(255, 255, 0, 0.9)",
						0.75, "rgba(255, 165, 0, 1.0)",
						1.0, "rgba(255, 0, 0, 1.0)"
					],

					// fade heatmap slightly at max zoom (optional)
					"heatmap-opacity": [
						"interpolate",
						["linear"],
						["zoom"],
						14, 0.95,
						18, 0.85
					]
				}
			},
			findFirstSymbolLayerId(map) || undefined
		);
	}
}

function setupPinLayer(map: MLMap) {
	// Create pin emoji image
	try {
		if (!(map as any).hasImage || !(map as any).hasImage("pin-emoji")) {
			const size = 90;
			const canvas = document.createElement("canvas");
			canvas.width = size;
			canvas.height = size;
			const ctx = canvas.getContext("2d");
			if (ctx) {
				ctx.clearRect(0, 0, size, size);
				ctx.textAlign = "center";
				ctx.textBaseline = "middle";
				ctx.font = `${Math.floor(size * 0.9)}px "Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif`;
				ctx.fillText("📍", size / 2, size / 2);
				const imgData = ctx.getImageData(0, 0, size, size);
				(map as any).addImage("pin-emoji", imgData, { pixelRatio: 2 });
			}
		}

		if (!map.getLayer("events-pins")) {
			(map as any).addLayer({
				id: "events-pins",
				type: "symbol",
				source: "events",
				minzoom: 12,
				layout: {
					"icon-image": "pin-emoji",
					"icon-size": [
						"interpolate",
						["linear"],
						["zoom"],
						12, 0.45,
						20, 0.8
					],
					"icon-allow-overlap": true,
					"icon-anchor": "bottom"
				}
			});
		}
	} catch (e) {
		// no-op if emoji image can't be created in this environment
	}
}