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
import TimelineIcon from "./TimelineIcon";

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
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const initialData = useMemo(
    () => toFeatureCollection((data ?? []).slice(0, maxClientPoints)),
    [data, maxClientPoints]
  );

  const search = useSearch();
  const filters = useFilters();
  const { categories } = useCategories();
  
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

  // Apply map layer filtering by selected categories
  useMapCategoryFilter(mapRef.current, filters.selectedCategories);

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
      const filtered = filters.isActive
        ? results.filter((e) => e.category && filters.selectedCategories.includes(e.category))
        : results;
      setPanel({ locationLabel: `Results for "${query}"`, events: filtered });
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

			{/* Search + Filter icons stack (top-right) */}
			<div style={{ position: "absolute", top: 12, right: panel ? 432 : 12, zIndex: 15 }}>
				<div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
					<SearchIcon onClick={search.openSearch} />
					<FilterIcon 
						active={filters.isActive}
						onClick={() => setIsFilterOpen(true)}
					/>
          <TimelineIcon onClick={() => {}}/>
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
          onClose={() => setPanel(null)}
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