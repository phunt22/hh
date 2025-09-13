import { useEffect, useState } from 'react';
import type { Map as MLMap, GeoJSONSource } from "maplibre-gl";
import { zoomToRadiusKm, toFeatureCollection, debounce } from '../utils/mapUtils';
import type { EventPoint } from '../types';

type UseMapViewportProps = {
	map: MLMap | null;
	onViewportQuery?: (center: { lat: number; lng: number }, radiusKm: number, viewport: any) => Promise<EventPoint[]>;
	fetchDebounceMs: number;
	maxClientPoints: number;
	data?: EventPoint[];
};

export function useMapViewport({
	map,
	onViewportQuery,
	fetchDebounceMs,
	maxClientPoints,
	data
}: UseMapViewportProps) {
	const [pointCount, setPointCount] = useState(0);

  useEffect(() => {
    if (!map || !onViewportQuery) return;

		const debounced = debounce(async () => {
			const c = map.getCenter();
			const z = map.getZoom();
			
			try {
				const rows = await onViewportQuery(
					{ lat: c.lat, lng: c.lng },
					zoomToRadiusKm(z),
					{ zoom: z, bearing: map.getBearing(), pitch: map.getPitch() }
				);
				
				// Update source with fetched data (cap to avoid perf cliffs)
				const capped = rows.slice(0, maxClientPoints);
				const src = map.getSource("events") as GeoJSONSource;
				src?.setData(toFeatureCollection(capped) as any);
				setPointCount(capped.length);
			} catch (error) {
				console.warn("Viewport query failed:", error);
			}
		}, fetchDebounceMs);

		map.on("moveend", debounced);

		return () => {
			map.off("moveend", debounced);
		};
	}, [map, onViewportQuery, fetchDebounceMs, maxClientPoints]);

	useEffect(() => {
		if (!map || !data || data.length === 0) return;

		const applyData = () => {
			const src = map.getSource("events") as GeoJSONSource | undefined;
			if (src) {
				const capped = data.slice(0, maxClientPoints);
				src.setData(toFeatureCollection(capped) as any);
				setPointCount(capped.length);
			}
		};

		// If style isn't loaded yet, wait for it before calling getSource
		const isLoaded = (map as any).isStyleLoaded && (map as any).isStyleLoaded();
		if (!isLoaded) {
			const onLoad = () => applyData();
			map.once("load", onLoad);
			return () => {
				map.off("load", onLoad);
			};
		}

		applyData();
	}, [map, data, maxClientPoints]);

	return { pointCount };
}

export function useMapControls(map: MLMap | null, initialView: any) {
	const doZoom = (factor: number) => {
		if (!map) return;
		const z = map.getZoom();
		map.easeTo({ zoom: Math.max(0.5, Math.min(20, z * factor)), duration: 250 });
	};

	const reset = () => {
		if (!map) return;
		map.easeTo({ 
			center: [initialView.lon, initialView.lat], 
			zoom: initialView.zoom, 
			bearing: 0, 
			pitch: 0, 
			duration: 400 
		});
	};

	return { doZoom, reset };
}