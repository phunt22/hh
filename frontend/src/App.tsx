import './App.css'
import Globe from './components/Globe'
import { EventsAPI } from './services/api'
import { DEFAULT_STYLE } from './constants/mapConstants'
import { useQuery } from '@tanstack/react-query';

const HYBRID = import.meta.env.VITE_MAPTILER_API_KEY
    ? `https://api.maptiler.com/maps/hybrid/style.json?key=${import.meta.env.VITE_MAPTILER_API_KEY}`
    : DEFAULT_STYLE;

function App() {  
  const handleViewportQuery = async (center: { lat: number; lng: number }, radiusKm: number) => {
    const rows = await EventsAPI.getEventsInViewport(center, radiusKm, 300);

    return rows;
  };

  const { data: events } = useQuery({
    queryKey: ["events"],
    queryFn: async () => {
      return EventsAPI.getEvents();
    }
  })

  return (
    <Globe
      data={events ?? []}
      mapStyle={HYBRID}
      onViewportQuery={handleViewportQuery}
      startAtUserLocation
    />
  )
}

export default App;
