import type { Map as MLMap, PointLike } from "maplibre-gl";
import type { EventPoint } from '../types';

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
		const attendeesNum = (typeof props.attendance === "number" ? props.attendance : Number(props.attendance));
		
		onHoverChange({
			x: e.point?.x ?? 0,
			y: e.point?.y ?? 0,
			properties: {
				id: String(props.id ?? ""),
				title: String(props.title ?? "Event"),
				description: props.description || "",
				start: props.start || "",
				end: props.end || "",
				category: props.category || "",
				attendance: Number.isFinite(attendeesNum) ? attendeesNum : undefined
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

		// const coords = (feats[0]?.geometry?.coordinates ?? []) as [number, number];
		// const fallbackLabel = Array.isArray(coords) && coords.length >= 2 ?
		// 	`${coords[1].toFixed(5)}, ${coords[0].toFixed(5)}` : "Selected location";
		const fallbackLabel = String(feats[0]?.properties?.title || "Selected Events");

		
		const withLocation = feats.find((ff: any) => {
			const loc = (ff?.properties ?? {}).location;
			return typeof loc === 'string' && loc.trim().length > 0;
		});
		const locationLabel = String(withLocation.properties?.city || (withLocation?.properties?.location as any) || fallbackLabel);

		// collect events overlapping locations		
		const events: EventPoint[] = feats.map((f: any) => {
			const p = f.properties || {};
			const c = f.geometry?.coordinates || [];
			const lon = Array.isArray(c) ? Number(c[0]) : NaN;
			const lat = Array.isArray(c) ? Number(c[1]) : NaN;
			const attendeesNum = typeof (p as any).attendance === "number" ? (p as any).attendance : Number((p as any).attendance);
			
			// find original event to restore similarEvents (only from provided data)
			const originalEvent = (data ?? []).find(e => e.id === p.id);
			
			return {
				id: String(p.id ?? Math.random().toString(36).slice(2)),
				title: String(p.title ?? "Event"),
				lat: Number.isFinite(lat) ? lat : 0,
				lng: Number.isFinite(lon) ? lon : 0,
				description: p.description || "",
				start: (p as any).start || undefined,
				end: (p as any).end || undefined,
				category: p.category || "",
				location: p.location || locationLabel,
				attendance: Number.isFinite(attendeesNum) ? attendeesNum : undefined,
				similarEvents: originalEvent?.similarEvents || undefined
			} as EventPoint;
		});

		onHoverChange(null);
		onPanelChange({ locationLabel, events });
	});
}