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
import FilterIcon from './FilterIcon';
import FilterOverlay from './FilterOverlay';
import { useFilters } from '../hooks/useFilters';
import { useMapCategoryFilter } from '../hooks/useMapCategoryFilter';
import { useCategories } from '../hooks/useCategories';

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
  const [panel, setPanel] = useState<{ locationLabel: string; events: EventPoint[]; isSearch?: boolean } | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const initialData = useMemo(
    () => toFeatureCollection((data ?? []).slice(0, maxClientPoints)),
    [data, maxClientPoints]
  );

  const search = useSearch();
  const filters = useFilters();
  const { categories } = useCategories();
  
  const displayedData: EventPoint[] = search.isSearchActive ? (search.searchResults ?? []) : (data ?? []);

  const { containerRef, mapRef } = useMapInstance({
    mapStyle,
    initialView,
    initialData,
    startAtUserLocation,
    onToast: setToastMessage,
    onHoverChange: setHoverInfo,
    onPanelChange: setPanel,
    data: displayedData
  });

  // Apply map layer filtering by selected categories, but override while searching
  useMapCategoryFilter(mapRef.current, search.isSearchActive ? [] : filters.selectedCategories);

  useMapViewport({
    map: mapRef.current,
    onViewportQuery: search.isSearchActive ? undefined : onViewportQuery,
    fetchDebounceMs,
    maxClientPoints,
    data: displayedData
  });

	const { doZoom, reset } = useMapControls(mapRef.current, initialView);

  const fitMapToResults = (results: EventPoint[]) => {
    const map = mapRef.current;
    if (!map || !results || results.length === 0) return;
    const valid = results.filter(r => Number.isFinite(r.lat) && Number.isFinite(r.lng) && !(r.lat === 0 && r.lng === 0));
    if (valid.length === 0) return;

    if (valid.length === 1) {
      const one = valid[0];
      map.easeTo({ center: [one.lng, one.lat], zoom: Math.max(12, map.getZoom()), duration: 500 });
      return;
    }

    let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;
    for (const r of valid) {
      if (r.lng < minLng) minLng = r.lng;
      if (r.lng > maxLng) maxLng = r.lng;
      if (r.lat < minLat) minLat = r.lat;
      if (r.lat > maxLat) maxLat = r.lat;
    }
    try {
      map.fitBounds([[minLng, minLat], [maxLng, maxLat]] as any, { padding: 80, duration: 600 });
    } catch {
      // ignore
    }
  };

  const handleSearchExecute = async (query: string) => {
    const result = await search.executeSearch(query);
    if (result.success) {
      const results = (result as any).results as EventPoint[];
      if (!results || results.length === 0) {
        setToastMessage(`No results for "${query}"`);
        search.closeSearch();
        return;
      }
      setPanel({ locationLabel: `Results for "${query}"`, events: results, isSearch: true });
      fitMapToResults(results);
    } else {
      const msg = (result as any).error || 'Search failed';
      setToastMessage(msg);
    }
    search.closeSearch();
  };

  // move the user to the event
  const handleEventClick = (e: EventPoint) => {
    const map = mapRef.current;
    if (!map) return;
    if (Number.isFinite(e.lng) && Number.isFinite(e.lat)) {
      map.easeTo({ center: [e.lng, e.lat], zoom: Math.max(10, map.getZoom()), duration: 900 });
    }
  };

	return (
		<div style={{ position: "relative", width: "100vw", height: "100vh", ...style }}>
			<div ref={containerRef} style={{ position: "absolute", inset: 0 }} />

			{toastMessage && (
				<Toast message={toastMessage} duration={3000} onClose={() => setToastMessage(null)} />
			)}

			<div style={{ position: "absolute", top: 12, right: panel ? 432 : 12, zIndex: 15 }}>
				<div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
					<SearchIcon 
				onClick={search.openSearch} 
				/>
					<FilterIcon 
						active={filters.isActive}
						onClick={() => setIsFilterOpen(true)}
					/>
				</div>
			</div>
			
			{showControls && (
				<Controls onZoomIn={() => doZoom(2)} onZoomOut={() => doZoom(0.5)} onReset={reset} />
			)}

      <HoverModal info={hoverInfo} />

      {panel && (
        <EventListPanel
          locationLabel={panel.locationLabel}
          events={panel.events}
          isSearchResults={panel.isSearch === true}
          onEventClick={handleEventClick}
          onClose={() => {
            if (panel?.isSearch) {
              search.clearSearch();
            }
            setPanel(null);
          }}
        />
      )}

      <SearchOverlay
        isOpen={search.isSearchOpen}
        onClose={search.closeSearch}
        onSearch={handleSearchExecute}
      />

      <FilterOverlay
        isOpen={isFilterOpen}
        onClose={() => setIsFilterOpen(false)}
        selectedCategories={filters.selectedCategories}
        onToggleCategory={filters.toggleCategory}
        onSelectAll={() => filters.setCategories(categories)}
        onClearAll={filters.clearAll}
        categories={categories}
      />
    </div>
  );
}