import { useMemo, useState } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GlobeProps } from '../types';
import { toFeatureCollection } from '../utils/mapUtils';
import { DEFAULT_STYLE, DEFAULT_VIEW } from '../constants/mapConstants';
import { useMapInstance } from '../hooks/useMapInstance';
import { useMapViewport, useMapControls } from '../hooks/useMapViewport';
import { useSearch } from '../hooks/useSearch';
import type { EventPoint } from '../types';
import Toast from './Toast';
import Controls from './Controls';
import HoverModal, { type HoverInfo } from "./HoverModal";
import EventListPanel from "./EventListPanel";
import SearchIcon from './SearchIcon';
import SearchOverlay from './SearchOverlay';

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
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [hoverInfo, setHoverInfo] = useState<HoverInfo>(null);
  const [panel, setPanel] = useState<{ locationLabel: string; events: any[] } | null>(null);

  const initialData = useMemo(
    () => toFeatureCollection((data ?? []).slice(0, maxClientPoints)),
    [data, maxClientPoints]
  );

  const search = useSearch();
  
  const { containerRef, mapRef } = useMapInstance({
    mapStyle,
    initialView,
    initialData,
    startAtUserLocation,
    onToast: setToastMessage,
    onHoverChange: setHoverInfo,
    onPanelChange: setPanel,
    data
  });

	useMapViewport({
    map: mapRef.current,
    onViewportQuery,
    fetchDebounceMs,
    maxClientPoints,
    data
	});

	const { doZoom, reset } = useMapControls(mapRef.current, initialView);

  const handleSearchExecute = async (query: string) => {
    const result = await search.executeSearch(query);
    if (result.success) {
      // open panel to show results
      const results = (result as any).results as EventPoint[];
      setPanel({ locationLabel: `Results for "${query}"`, events: results });
    } else {
      setToastMessage('Search failed');
    }
    search.closeSearch();
  };

	return (
		<div style={{ position: "relative", width: "100vw", height: "100vh", ...style }}>
			<div ref={containerRef} style={{ position: "absolute", inset: 0 }} />

			{toastMessage && (
				<Toast message={toastMessage} duration={3000} onClose={() => setToastMessage(null)} />
			)}

			{/* Search icon */}
			<SearchIcon 
				onClick={search.openSearch} 
				style={{ 
					position: "absolute", 
					top: 12, 
					right: panel ? 432 : 12, // Inside sidebar when panel is open
					zIndex: 15
				}} 
			/>
			
			{showControls && (
				<Controls onZoomIn={() => doZoom(2)} onZoomOut={() => doZoom(0.5)} onReset={reset} />
			)}

      <HoverModal info={hoverInfo} />

      {panel && (
        <EventListPanel
          locationLabel={panel.locationLabel}
          events={panel.events}
          onClose={() => setPanel(null)}
        />
      )}

      <SearchOverlay
        isOpen={search.isSearchOpen}
        onClose={search.closeSearch}
        onSearch={handleSearchExecute}
      />
    </div>
  );
}