// NOT USED
// Here if ever needed

import Globe from 'react-globe.gl';
import { useEffect, useRef, useState } from 'react';
import * as topojson from 'topojson-client';

// some sample data
const SAMPLE_DATA = [
    { lat: 40.7128, lng: -74.006, value: 100 },
    { lat: 48.8566, lng: 2.3522, value: 80 },
    { lat: 35.6895, lng: 139.6917, value: 60 },
    { lat: 51.5074, lng: -0.1278, value: 90 },
    { lat: -33.8688, lng: 151.2093, value: 70 },
];

// demo cities
const CITIES = [
    { name: "New York", lat: 40.7128, lng: -74.0060 },
    { name: "London", lat: 51.5074, lng: -0.1278 },
    { name: "Paris", lat: 48.8566, lng: 2.3522 },
    { name: "Tokyo", lat: 35.6895, lng: 139.6917 },
    { name: "Sydney", lat: -33.8688, lng: 151.2093 },
    { name: "São Paulo", lat: -23.5558, lng: -46.6396 },
    { name: "Nairobi", lat: -1.2921, lng: 36.8219 }
];

export default function GlobeComponent() {
    const globeRef = useRef<any>(null);
    const [borders, setBorders] = useState<any[]>([]);
    const [showCities, setShowCities] = useState<boolean>(false);

    

    // load borders only once
    useEffect(() => {
        fetch('https://unpkg.com/world-atlas@2/countries-110m.json')
            .then(res => res.json())
            .then((topology) => {
                const geojson: any = topojson.feature(topology, (topology as any).objects.countries);
                setBorders(Array.isArray((geojson as any).features) ? (geojson as any).features : []);
            })
            .catch(() => setBorders([]));
    }, []);

    useEffect(() => {
        if (!globeRef.current) return;

        const avgLat = SAMPLE_DATA.reduce((s, d) => s + d.lat, 0) / SAMPLE_DATA.length;
        const avgLng = SAMPLE_DATA.reduce((s, d) => s + d.lng, 0) / SAMPLE_DATA.length;

        // Zoom towards your data centroid
        globeRef.current.pointOfView({ lat: avgLat, lng: avgLng, altitude: 0.8 }, 1000);

        // Optional: tune zoom limits and speed via OrbitControls
        const controls = globeRef.current.controls?.();
        const radius = globeRef.current.getGlobeRadius?.() ?? 100;
        if (controls) {
            controls.minDistance = radius * 1.05;
            controls.maxDistance = radius * 6;
            controls.zoomSpeed = 0.6;
        }
    }, []);

    const zoomByFactor = (factor: number) => {
        if (!globeRef.current) return;
        const pov = globeRef.current.pointOfView?.() || { lat: 0, lng: 0, altitude: 2.5 };
        const nextAltitude = Math.max(0.1, Math.min(10, (pov.altitude ?? 2.5) * factor));
        globeRef.current.pointOfView({ lat: pov.lat, lng: pov.lng, altitude: nextAltitude }, 500);
    };

    const resetView = () => {
        if (!globeRef.current) return;
        const avgLat = SAMPLE_DATA.reduce((s, d) => s + d.lat, 0) / SAMPLE_DATA.length;
        const avgLng = SAMPLE_DATA.reduce((s, d) => s + d.lng, 0) / SAMPLE_DATA.length;
        globeRef.current.pointOfView({ lat: avgLat, lng: avgLng, altitude: 1.2 }, 800);
    };

    const toggleAutoRotate = () => {
        const controls = globeRef.current?.controls?.();
        if (!controls) return;
        controls.autoRotate = !controls.autoRotate;
        controls.autoRotateSpeed = 0.5;
        controls.update();
    };

    return (
        <div style={{ width: "100%", height: "100%", position: "relative" }}>
            <Globe
                ref={globeRef}
                width={window.innerWidth}
                height={window.innerHeight}
                backgroundColor="#000000"
                globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
                backgroundImageUrl=""
                pointsData={SAMPLE_DATA}
                pointLat="lat"
                pointLng="lng"
                pointColor="value"
                pointRadius={0.5}
                pointResolution={15}
                pointAltitude={0.01}
                enablePointerInteraction={true}
                // showAtmosphere={true}
                atmosphereColor="#3a5a78"
                atmosphereAltitude={0.15}
                onPointClick={(p: any) => globeRef.current?.pointOfView({ lat: p.lat, lng: p.lng, altitude: 0.6 }, 800)}
                onZoom={() => {
                    const pov = globeRef.current?.pointOfView?.();
                    const altitude = pov?.altitude ?? 2.5;
                    setShowCities(altitude < 1.2);
                }}
                polygonsData={borders}
                polygonCapColor={() => "rgba(0,0,0,0)"}
                polygonSideColor={() => "rgba(255,255,255,0.15)"}
                polygonStrokeColor={() => "rgba(255,255,255,0.6)"}
                polygonAltitude={0.002}
                labelsData={showCities ? CITIES : []}
                labelLat="lat"
                labelLng="lng"
                labelText="name"
                labelSize={1.4}
                labelColor={() => "#ffffff"}
                labelDotRadius={0.2}
            />
            <div style={{ position: "absolute", bottom: 12, right: 12, display: "flex", gap: 8 }}>

                <button onClick={() => zoomByFactor(2.0)} style={{ padding: "8px 12px", background: "#111", color: "#fff", border: "1px solid #333" }}>-
                </button>

                <button onClick={() => zoomByFactor(0.5)} style={{ padding: "8px 12px", background: "#111", color: "#fff", border: "1px solid #333" }}>+
                </button>
                
                <button onClick={resetView} style={{ padding: "8px 12px", background: "#111", color: "#fff", border: "1px solid #333" }}>Reset
                </button>
                <button onClick={toggleAutoRotate} style={{ padding: "8px 12px", background: "#111", color: "#fff", border: "1px solid #333" }}>Auto-rotate
                </button>
            </div>
        </div>
    )
}