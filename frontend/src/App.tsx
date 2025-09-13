import './App.css'
import Globe from './components/Globe'
import { EventsAPI } from './services/api'

function App() {
  const HYBRID = `https://api.maptiler.com/maps/hybrid/style.json?key=${import.meta.env.VITE_MAPTILER_API_KEY}`;
  
  const handleViewportQuery = async (center: { lat: number; lng: number }, radiusKm: number) => {
    const rows = await EventsAPI.getEventsInViewport(center, radiusKm, 300);

    return rows;
  };

  return (
    <Globe
      mapStyle={HYBRID}
      onViewportQuery={handleViewportQuery}
      startAtUserLocation
    />
  )
}

export default App;
