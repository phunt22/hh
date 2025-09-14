import { useMemo, useRef, useState } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GlobeProps } from '../types';
import { toFeatureCollection } from '../utils/mapUtils';
import { DEFAULT_STYLE, DEFAULT_VIEW } from '../constants/mapConstants';
import { useMapInstance } from '../hooks/useMapInstance';
import { useMapViewport } from '../hooks/useMapViewport';
import { useSearch } from '../hooks/useSearch';
import type { EventPoint } from '../types';
import Toast from './Toast';
import HoverModal, { type HoverInfo } from "./HoverModal";
import EventListPanel from "./EventListPanel";
import SearchIcon from './SearchIcon';
import SearchOverlay from './SearchOverlay';
import FilterIcon from './FilterIcon';
import FilterOverlay from './FilterOverlay';
import TrendIcon from './TrendIcon';
import { useFilters } from '../hooks/useFilters';
import { useMapCategoryFilter } from '../hooks/useMapCategoryFilter';
import { useCategories } from '../hooks/useCategories';
import { EventsAPI, type BusiestCity } from '../services/api';
import TimelineIcon from "./TimelineIcon";
import TimelineSlider from "./TimelineSlider";
import { AudioPlayerWithVisualizer } from "./AudioPlayer";
import {BusiestCitiesChart} from './BusiestCitiesChart';

export default function Globe({
  data,
  onViewportQuery,
  mapStyle = DEFAULT_STYLE,
  initialView = DEFAULT_VIEW,
  maxClientPoints = 40000,
  fetchDebounceMs = 220,
  style,
}: GlobeProps) {
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [hoverInfo, setHoverInfo] = useState<HoverInfo>(null);
  const [panel, setPanel] = useState<{ locationLabel: string; events: EventPoint[]; isSearch?: boolean } | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isTimelineActive, setIsTimelineActive] = useState(false);
  const [currentTimelineIndex, setCurrentTimelineIndex] = useState<number>(0);
  const [isPanelClosing, setIsPanelClosing] = useState(false);
  const [busiestCities, setBusiestCities] = useState<BusiestCity[]>([]);
  const [isLoadingBusiestCities, setIsLoadingBusiestCities] = useState(false);

  const timelineIntervalRef = useRef<number | null>(null);

  const initialData = useMemo(
    () => toFeatureCollection((data ?? []).slice(0, maxClientPoints)),
    [data, maxClientPoints]
  );

  //const [timelineData, setTimelineData] = useState<EventPoint[]>([]);
  
  const search = useSearch();
  const filters = useFilters();
  const { categories } = useCategories();
  
  
  // Group events into 3-hour intervals between min and max (start/end) times.
  const timelineGroupedData = useMemo(() => {
    if (!Array.isArray(data) || data.length === 0) return [];

    // Get all valid times (start and end) as timestamps
    const times: number[] = [];
    for (const event of data) {
      if (event.start) times.push(new Date(event.start).getTime());
      if (event.end) times.push(new Date(event.end).getTime());
    }
    if (times.length === 0) return [];

    // Find min and max time
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);

    // 30 minutes in ms
    const intervalMs = 15 * 60 * 1000;

    // Build intervals: [ [start, end), ... ]
    const intervals: Array<{ start: number, end: number }> = [];
    for (let t = minTime; t < maxTime; t += intervalMs) {
      intervals.push({ start: t, end: t + intervalMs });
    }

    // For each interval, collect events that are active (start <= interval.end && end >= interval.start)
    // If event.end is missing, treat as a point event at start
    const grouped: EventPoint[][] = intervals.map(({ start, end }) => {
      return data.filter(event => {
        const eventStart = event.start ? new Date(event.start).getTime() : null;
        const eventEnd = event.end ? new Date(event.end).getTime() : eventStart;
        if (eventStart === null) return false;
        // Event is active if it overlaps with the interval
        return eventStart < end && (eventEnd ?? eventStart) >= start;
      });
    });
    return grouped;
  }, [data]);

  const displayedData: EventPoint[] = isTimelineActive
    ? (
        currentTimelineIndex === 0
          ? (timelineGroupedData[0] || [])
          : (timelineGroupedData[currentTimelineIndex - 1] || []).concat(timelineGroupedData[currentTimelineIndex] || [])
      )
    : 
  search.isSearchActive ? (search.searchResults ?? []) : (data ?? []);

  const { containerRef, mapRef } = useMapInstance({
    mapStyle,
    initialView,
    initialData,
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

  const fitMapToResults = (results: EventPoint[]) => {
    const map = mapRef.current;
    if (!map || !results || results.length === 0) return;
    const valid = results.filter(r => Number.isFinite(r.lat) && Number.isFinite(r.lng) && !(r.lat === 0 && r.lng === 0));
    if (valid.length === 0) return;

    if (valid.length === 1) {
      const one = valid[0];
      map.easeTo({ center: [one.lng, one.lat], zoom: Math.max(12, map.getZoom()), duration: 900 });
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
      map.fitBounds([[minLng, minLat], [maxLng, maxLat]] as any, { padding: 80, duration: 900 });
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

 

  const toggleTimeline = () => {
    if (isTimelineActive) {
      // Stop
      setIsTimelineActive(false);
      setCurrentTimelineIndex(0);
      if (timelineIntervalRef.current) {
        clearInterval(timelineIntervalRef.current);
        timelineIntervalRef.current = null;
      }
    } else {
      // Start
      setIsTimelineActive(true);
      setPanel(null);
      search.clearSearch();
      setIsFilterOpen(false);
  
      setCurrentTimelineIndex(0);
      timelineIntervalRef.current = window.setInterval(() => {
        setCurrentTimelineIndex(prevIndex => {
          if (!timelineGroupedData || timelineGroupedData.length === 0) return 0;
          if (prevIndex >= timelineGroupedData.length - 1) {
            clearInterval(timelineIntervalRef.current!);
            timelineIntervalRef.current = null;
            return prevIndex;
          }
          return prevIndex + 1;
        });
      }, 700);
    }
  };
  
  // Update your handleBusiestCitiesClick function in Globe.tsx
  const handleBusiestCitiesClick = async () => {
    if (busiestCities.length > 0) {
      // If we already have data, show it
      console.log('Using cached cities:', busiestCities);
      const allEvents = busiestCities.flatMap((city: BusiestCity) => 
        city.top_events.map((event: any) => ({
          id: event.id,
          title: event.title,
          lat: event.latitude || 0,
          lng: event.longitude || 0,
          description: event.description,
          attendance: event.attendance || 0,
          start: event.start,
          end: event.end,
          category: event.category,
          location: event.location,
        }))
      );
      setPanel({ 
        locationLabel: `Busiest Cities (${busiestCities.length} cities)`, 
        events: allEvents 
      });
      return;
    }

    setIsLoadingBusiestCities(true);
    try {
      console.log('🔄 Fetching busiest cities...');
      const cities = await EventsAPI.getBusiestCities({ limit: 10, time_window_days: 7 });
      
      // DEBUG: Let's see what we actually got
      console.log('✅ Raw API Response:', cities);
      console.log('📊 Number of cities returned:', cities.length);
      
      // Log each city's details
      cities.forEach((city, index) => {
        console.log(`🏙️  City ${index + 1}: ${city.city}`);
        console.log(`   Total attendance: ${city.total_attendance}`);
        console.log(`   Events: ${city.top_events}`);
        console.log(`   Event Count:`, city.event_counts);
        console.log('---');
      });
      
      setBusiestCities(cities);
      
      // Convert to EventPoint format for display
      const allEvents = cities.flatMap((city: BusiestCity) => 
        city.top_events.map((event: any) => ({
          id: event.id,
          title: event.title,
          lat: event.latitude || 0,
          lng: event.longitude || 0,
          description: event.description,
          attendance: event.attendance || 0,
          start: event.start,
          end: event.end,
          category: event.category,
          location: event.location,
        }))
      );
      
      console.log('🎯 Total events from all cities:', allEvents.length);
      
      setPanel({ 
        locationLabel: `Busiest Cities (${cities.length} cities)`, 
        events: allEvents 
      });
      
      // Fit map to show all busiest cities
      fitMapToResults(allEvents);
      
    } catch (error) {
      console.error('❌ Error fetching busiest cities:', error);
      setToastMessage('Busiest cities feature is temporarily unavailable. The backend needs more event data with attendance information.');
      
      // Show a fallback with some sample data for demonstration
      const fallbackEvents = (data ?? []).slice(0, 10).map(event => ({
        id: event.id,
        title: event.title,
        lat: event.lat,
        lng: event.lng,
        description: event.description,
        attendance: event.attendance,
        start: event.start,
        end: event.end,
        category: event.category,
        location: event.location,
      }));
      
      setPanel({ 
        locationLabel: 'Sample Events (Busiest Cities feature coming soon)', 
        events: fallbackEvents 
      });
    } finally {
      setIsLoadingBusiestCities(false);
    }
  };
  
  return (
		<div style={{ position: "relative", width: "100vw", height: "100vh", ...style }}>
			<div ref={containerRef} style={{ position: "absolute", inset: 0 }} />

			{toastMessage && (
				<Toast message={toastMessage} duration={3000} onClose={() => setToastMessage(null)} />
			)}

			<div style={{ position: "absolute", top: 12, marginTop: 3, right: panel ? (isPanelClosing ? 12 : 504) : 12, zIndex: 15, transition: 'right 180ms ease, transform 180ms ease', transform: isPanelClosing ? 'translateX(16px) scale(0.98)' : 'translateX(0) scale(1)' }}>
				<div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 0 }}>
					<SearchIcon onClick={search.openSearch} />
					<FilterIcon
						active={filters.isActive}
						onClick={() => setIsFilterOpen(true)}
					/>
          <TimelineIcon active={isTimelineActive} onClick={toggleTimeline}/>
					<TrendIcon 
						onClick={handleBusiestCitiesClick}
						disabled={isLoadingBusiestCities}
						title={isLoadingBusiestCities ? 'Loading...' : 'Show Busiest Cities (Demo Mode)'}
					/>
				</div>
			</div>
			
      <HoverModal info={hoverInfo} />

      {panel && (
        <>
          <EventListPanel
            header={busiestCities.length > 0 && <BusiestCitiesChart busiestCities={busiestCities} />}
            locationLabel={panel.locationLabel}
            events={panel.events}
            isSearchResults={panel.isSearch === true}
            onEventClick={handleEventClick}
            onClosingChange={setIsPanelClosing}
            onClose={() => {
              if (panel?.isSearch) {
                search.clearSearch();
              }
              setPanel(null);
            }}
          />
        </>
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

      {
        isTimelineActive && (
          <TimelineSlider
            minIndex={0}
            maxIndex={timelineGroupedData.length - 1}
            value={currentTimelineIndex}
            onChange={setCurrentTimelineIndex}
          />
        )
      }

      {
        search.isSearchActive && search.audioUrl && (
          <AudioPlayerWithVisualizer audioDataUrl={search.audioUrl} />
        )
      }
    </div>
  );
}