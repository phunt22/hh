import './App.css'
import Globe from './components/Globe'
import { SAMPLE_EVENTS } from './constants/mapConstants'

function App() {
  const HYBRID = `https://api.maptiler.com/maps/hybrid/style.json?key=${import.meta.env.VITE_MAPTILER_API_KEY}`;
  
  // TODO IMPLEMENT
  const handleViewportQuery = async (_center: { lat: number; lng: number }, _radiusKm: number) => {
    // TODO IMPLEMENT

    // simulate api delay
    await new Promise(resolve => setTimeout(resolve, 100));
    return SAMPLE_EVENTS;
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
