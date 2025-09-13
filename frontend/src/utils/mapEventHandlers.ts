import type { Map as MLMap, PointLike } from "maplibre-gl";
import type { EventPoint } from '../types';
import { SAMPLE_EVENTS } from '../constants/mapConstants';

export function setupMapEventHandlers(
	map: MLMap,
	onHoverChange: (info: any) => void,
	onPanelChange: (panel: any) => void,
	data?: EventPoint[]
) {
    map.on("mouseenter", "events-pins", () => {
        map.getCanvas().style.cursor = "pointer";
    });

    map.on("mouseleave", "events-pins", () => {
        map.getCanvas().style.cursor = "";
        onHoverChange(null);
    });

	map.on("mousemove", "events-pins", (e: any) => {
		const f = e?.features && e.features[0];
		if (!f || !f.properties) {
			onHoverChange(null);
			return;
		}
		
		const props = f.properties as any;
		const attendeesNum = typeof props.expectedAttendees === "number" ? props.expectedAttendees : Number(props.expectedAttendees);
		
		onHoverChange({
			x: e.point?.x ?? 0,
			y: e.point?.y ?? 0,
			properties: {
				id: String(props.id ?? ""),
				title: String(props.title ?? "Event"),
				description: props.description || "",
				time: props.time || "",
				category: props.category || "",
				expectedAttendees: Number.isFinite(attendeesNum) ? attendeesNum : undefined
			}
		});
	});

    map.on("click", "events-pins", (e: any) => {
        const r = 6; // px radius for overlap detection
        const bbox: [PointLike, PointLike] = [
        [Math.max(0, e.point.x - r), Math.max(0, e.point.y - r)],
        [e.point.x + r, e.point.y + r]
        ];
    
    const feats = map.queryRenderedFeatures(bbox, { layers: ["events-pins"] }) as any[];
    if (!feats || feats.length === 0) return;

		// Get location label from first feature
		const firstProps = (feats[0]?.properties ?? {}) as any;
		const coords = (feats[0]?.geometry?.coordinates ?? []) as [number, number];
		const fallbackLabel = Array.isArray(coords) && coords.length >= 2 ? 
			`${coords[1].toFixed(5)}, ${coords[0].toFixed(5)}` : "Selected location";
		const locationLabel = String(firstProps.location || firstProps.title || fallbackLabel);

            // collect events overlapping locations		
            const events: EventPoint[] = feats.map((f: any) => {
			const p = f.properties || {};
			const c = f.geometry?.coordinates || [];
			const lon = Array.isArray(c) ? Number(c[0]) : NaN;
			const lat = Array.isArray(c) ? Number(c[1]) : NaN;
			const attendeesNum = typeof p.expectedAttendees === "number" ? p.expectedAttendees : Number(p.expectedAttendees);
			
			// Find original event to restore similarEvents
			const originalEvent = (data ?? SAMPLE_EVENTS).find(e => e.id === p.id);
			
			return {
				id: String(p.id ?? Math.random().toString(36).slice(2)),
				title: String(p.title ?? "Event"),
				lat: Number.isFinite(lat) ? lat : 0,
				lng: Number.isFinite(lon) ? lon : 0,
				description: p.description || "",
				time: p.time || "",
				category: p.category || "",
				location: p.location || locationLabel,
				expectedAttendees: Number.isFinite(attendeesNum) ? attendeesNum : undefined,
				similarEvents: originalEvent?.similarEvents || undefined
			} as EventPoint;
		});

		onHoverChange(null);
		onPanelChange({ locationLabel, events });
	});
}