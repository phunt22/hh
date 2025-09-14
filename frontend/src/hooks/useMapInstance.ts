import { useEffect, useRef } from 'react';
import maplibregl, { Map as MLMap, type LngLatLike, type MapOptions } from "maplibre-gl";
import type { EventPoint } from '../types';
import { setupMapLayers } from '../utils/mapLayers';
import { setupMapEventHandlers } from '../utils/mapEventHandlers';

type UseMapInstanceProps = {
	mapStyle: string;
	initialView: { lon: number; lat: number; zoom: number; bearing?: number; pitch?: number };
	initialData: GeoJSON.FeatureCollection;
	onToast: (message: string) => void;
	onHoverChange: (info: any) => void;
	onPanelChange: (panel: any) => void;
	data?: EventPoint[];
};

export function useMapInstance({
	mapStyle,
	initialView,
	initialData,
	onHoverChange,
	onPanelChange,
	data
}: UseMapInstanceProps) {
	const containerRef = useRef<HTMLDivElement | null>(null);
	const mapRef = useRef<MLMap | null>(null);

	// Create map instance (only once on mount)
	useEffect(() => {
		if (!containerRef.current || mapRef.current) return;

		const opts: MapOptions = {
			container: containerRef.current,
			style: mapStyle,
			center: [initialView.lon, initialView.lat] as LngLatLike,
			zoom: initialView.zoom,
			bearing: initialView.bearing ?? 0,
			pitch: initialView.pitch ?? 0,
			fadeDuration: 0,
			attributionControl: { compact: false },
			interactive: true,
			cooperativeGestures: false
		};

		const map = new maplibregl.Map(opts);
		mapRef.current = map;

		map.on("load", () => {
			if (!map.getSource("events")) {
				map.addSource("events", {
					type: "geojson",
					data: initialData
				});
			}

			setupMapLayers(map);

			setupMapEventHandlers(map, onHoverChange, onPanelChange, data);
		});

		return () => {
			map.remove();
			mapRef.current = null;
		};
	}, []);

	return { containerRef, mapRef };
}
