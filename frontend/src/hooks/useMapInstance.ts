import { useEffect, useRef } from 'react';
import maplibregl, { Map as MLMap, type LngLatLike, type MapOptions } from "maplibre-gl";
import type { EventPoint } from '../types';
import { setupMapLayers } from '../utils/mapLayers';
import { setupMapEventHandlers } from '../utils/mapEventHandlers';

type UseMapInstanceProps = {
	mapStyle: string;
	initialView: { lon: number; lat: number; zoom: number; bearing?: number; pitch?: number };
	initialData: GeoJSON.FeatureCollection;
	startAtUserLocation: boolean;
	onToast: (message: string) => void;
	onHoverChange: (info: any) => void;
	onPanelChange: (panel: any) => void;
	data?: EventPoint[];
};

export function useMapInstance({
	mapStyle,
	initialView,
	initialData,
	startAtUserLocation,
	onToast,
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

			if (startAtUserLocation) {
				handleUserLocation(map, initialView, onToast);
			}
		});

		return () => {
			map.remove();
			mapRef.current = null;
		};
	}, []);

	return { containerRef, mapRef };
}

function handleUserLocation(
	map: MLMap, 
	initialView: any, 
	onToast: (message: string) => void
) {
	if (!navigator.geolocation) {
		onToast("Geolocation not supported in this browser.");
		return;
	}

	let resolved = false;
	
	const onSuccess = (pos: GeolocationPosition) => {
		if (resolved) return;
		resolved = true;
		const { latitude, longitude } = pos.coords;
		map.jumpTo({ center: [longitude, latitude], zoom: Math.max(10, initialView.zoom) });
	};
	
	const onFinalError = (err: GeolocationPositionError) => {
		if (resolved) return;
		resolved = true;
		const code = (err && (err as any).code) ?? 0;
		if (code === 1) {
			onToast("Location permission denied. Using default view.");
		} else if (code === 3) {
			onToast("Location timed out. Using default view.");
		} else {
			onToast("Couldn't access location. Using default view.");
		}
	};
	
	const tryCoarse = () => {
		if (resolved) return;
		navigator.geolocation.getCurrentPosition(
			onSuccess,
			onFinalError,
			{ enableHighAccuracy: false, timeout: 8000, maximumAge: 600000 }
		);
	};
	
	navigator.geolocation.getCurrentPosition(
		onSuccess,
		(err) => {
			const code = (err && (err as any).code) ?? 0;
			if (code === 1) {
				onFinalError(err);
			} else {
				tryCoarse();
			}
		},
		{ enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
	);
}
