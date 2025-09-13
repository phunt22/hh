import type { Map as MLMap } from "maplibre-gl";
import { findFirstSymbolLayerId } from './mapUtils';
import { ensureCategoryPins } from '../components/Pin';

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
					// weight: use attendace (0..5000 -> 0..1)
					"heatmap-weight": [
						"interpolate",
						["linear"],
						["coalesce", ["to-number", ["get", "attendance"]], 0],
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
	// Use colored SVG pins per category
	try {
		if (!map.getLayer("events-pins")) {
			(map as any).addLayer({
				id: "events-pins",
				type: "symbol",
				source: "events",
				minzoom: 4,
				layout: {
					"icon-image": ["concat", "pin-", ["get", "category"]],
					"icon-size": [
						"interpolate",
						["linear"],
						["zoom"],
						12, 0.8,
						20, 1.3
					],
					"icon-allow-overlap": true,
					"icon-anchor": "bottom"
				}
			});
		}

		ensureCategoryPins(map);

		// listen for data changes to add icons for new categories
		const handlerKey = "__eventsPinsSeedHandler";
		if (!(map as any)[handlerKey]) {
			const onSourceData = (e: any) => {
				if (!e || e.sourceId !== "events") return;
				ensureCategoryPins(map);
			};
			(map as any)[handlerKey] = onSourceData;
			map.on("sourcedata", onSourceData);
		}
	} catch (e) {
		// no-op in non-browser environments
	}
}