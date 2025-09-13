import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl, { Map as MLMap, GeoJSONSource, type LngLatLike, type MapOptions } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GlobeProps } from '../types';
import { zoomToRadiusKm, toFeatureCollection, debounce, findFirstSymbolLayerId } from '../utils/mapUtils';
import { DEFAULT_STYLE, DEFAULT_VIEW, SAMPLE_EVENTS } from '../constants/mapConstants';
import Toast from './Toast';
import Controls from './Controls';

export default function Globe({
  data,
  onViewportQuery,
  mapStyle = DEFAULT_STYLE,
  initialView = DEFAULT_VIEW,
  maxClientPoints = 40000,
  fetchDebounceMs = 220,
  showControls = false,
  style,
  startAtUserLocation = false
}: GlobeProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MLMap | null>(null);
  const [, setPointCount] = useState(0);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (message: string) => {
    setToastMessage(message);
  };

  const initialData = useMemo(
    () => toFeatureCollection((data ?? SAMPLE_EVENTS).slice(0, maxClientPoints)),
    [data, maxClientPoints]
  );

  // Create map once
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
      cooperativeGestures: false // no cmd to scroll
    };

    const map = new maplibregl.Map(opts);
    mapRef.current = map;

    map.on("load", () => {
        // set projection (not functional rn)
        // try {
        //     // (map as any).setProjection({ name: "globe" });
        // } catch { 
        //     console.log("projection failed") 
        // }

      
      if (!map.getSource("events")) {
        map.addSource("events", {
          type: "geojson",
          data: initialData
        });
      }

      // Heatmap layer (WebGL, very fast). Styling mimics Google’s red core/blue edges.
      if (!map.getLayer("events-heat")) {
        map.addLayer(
          {
            id: "events-heat",
            type: "heatmap",
            source: "events",
            maxzoom: 18,
            paint: {
              // weight: use popularity linearly (0..100 -> 0..1)
              "heatmap-weight": [
                "interpolate",
                ["linear"],
                ["coalesce", ["to-number", ["get", "popularity"]], 0],
                0, 0,
                100, 1
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
          // render above labels but below symbols if the style has such layers
          findFirstSymbolLayerId(map) || undefined
        );
      }


      // add a pin emoji symbol when zoomed in closely
      try {
        if (!(map as any).hasImage || !(map as any).hasImage("pin-emoji")) {
          const size = 100;
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
            minzoom: 11, // TODO maybe make this smaller (would show closer)
            layout: {
              "icon-image": "pin-emoji",
              "icon-size": [
                "interpolate",
                ["linear"],
                ["zoom"],
                11, 0.45,
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

      setPointCount((initialData.features ?? []).length);

      if (startAtUserLocation) {
        if (navigator.geolocation) {
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
              showToast("Location permission denied. Using default view.");
            } else if (code === 3) {
              showToast("Location timed out. Using default view.");
            } else {
              showToast("Couldn't access location. Using default view.");
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
        } else {
          showToast("Geolocation not supported in this browser.");
        }
      }
    });

    // debounced fetch on move end
    // this way we only grab the points/cities when user is done moving
    const debounced = debounce(async () => {
      if (!onViewportQuery) return;
      
      const c = map.getCenter();
      const z = map.getZoom();
      
      try {
        const rows = await onViewportQuery(
          { lat: c.lat, lng: c.lng },
          zoomToRadiusKm(z),
          { zoom: z, bearing: map.getBearing(), pitch: map.getPitch() }
        );
        
        // update source with fetched data (cap to avoid perf cliffs). Cap defined above
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
      map.remove();
      mapRef.current = null;
    };
  }, [mapStyle, initialView.lon, initialView.lat, initialView.zoom, initialView.bearing, initialView.pitch, onViewportQuery, fetchDebounceMs, maxClientPoints, initialData, startAtUserLocation]);

  // no timer cleanup needed; Toast handles its own lifecycle

  // update source if data prop changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !data) return;
    const src = map.getSource("events") as GeoJSONSource | undefined;
    if (src) {
      const capped = data.slice(0, maxClientPoints);
      src.setData(toFeatureCollection(capped) as any);
      setPointCount(capped.length);
    }
  }, [data, maxClientPoints]);

  // Controls
  const doZoom = (factor: number) => {
    const map = mapRef.current;
    if (!map) return;
    const z = map.getZoom();
    map.easeTo({ zoom: Math.max(0.5, Math.min(20, z * factor)), duration: 250 });
  };
  const reset = () => {
    const map = mapRef.current;
    if (!map) return;
    map.easeTo({ center: [initialView.lon, initialView.lat], zoom: initialView.zoom, bearing: 0, pitch: 0, duration: 400 });
  };

  return (
    <div style={{ position: "relative", width: "100vw", height: "100vh", ...style }}>
      <div ref={containerRef} style={{ position: "absolute", inset: 0 }} />

      {toastMessage && (
        <Toast message={toastMessage} duration={3000} onClose={() => setToastMessage(null)} />
      )}
      
      {showControls && (
        <Controls onZoomIn={() => doZoom(2)} onZoomOut={() => doZoom(0.5)} onReset={reset} />
      )}
    </div>
  );
}

