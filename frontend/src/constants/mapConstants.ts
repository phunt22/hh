import type { EventPoint } from '../types';

// free with no key
export const DEFAULT_STYLE = "https://demotiles.maplibre.org/style.json";

// SF VIEW
export const DEFAULT_VIEW = { lon: -122.4194, lat: 37.7749, zoom: 11, bearing: 0, pitch: 0 };

// WORLD VIEW
export const WORLD_VIEW = { lon: 0, lat: 20, zoom: 1, bearing: 0, pitch: 0 };

// TODO replace with real data
export const SAMPLE_EVENTS: EventPoint[] = [
  { 
    id: "1", 
    title: "Union Square Holiday Market", 
    lat: 37.7879, 
    lng: -122.4074, 
    expectedAttendees: 2500,
    category: "Shopping",
    description: "Annual holiday market featuring local artisans, food vendors, and festive entertainment in the heart of downtown San Francisco.",
    time: "2024-12-15T10:00:00Z",
    location: "Union Square",
    similarEvents: [
      { id: "1a", title: "Pier 39 Holiday Market", lat: 37.8085, lng: -122.4098, category: "Shopping", time: "2024-12-16T11:00:00Z", expectedAttendees: 1800 },
      { id: "1b", title: "Ferry Building Holiday Fair", lat: 37.7955, lng: -122.3937, category: "Shopping", time: "2024-12-17T09:00:00Z", expectedAttendees: 1200 }
    ]
  },
  { 
    id: "2", 
    title: "Market Street Food Festival", 
    lat: 37.7837, 
    lng: -122.4089, 
    expectedAttendees: 1800,
    category: "Food & Drink",
    description: "Street food festival showcasing SF's diverse culinary scene with over 50 food trucks and vendors.",
    time: "2024-12-20T12:00:00Z",
    location: "Market Street",
    similarEvents: [
      { id: "2a", title: "Off the Grid: Fort Mason", lat: 37.8059, lng: -122.4324, category: "Food & Drink", time: "2024-12-21T17:00:00Z", expectedAttendees: 900 }
    ]
  },
  { 
    id: "3", 
    title: "SoMa Art Walk", 
    lat: 37.7786, 
    lng: -122.4059, 
    expectedAttendees: 650,
    category: "Arts & Culture",
    description: "Monthly art walk featuring galleries, studios, and pop-up exhibitions throughout the South of Market district.",
    time: "2024-12-18T18:00:00Z",
    location: "SoMa District"
  },
  { 
    id: "4", 
    title: "Mission District Block Party", 
    lat: 37.7599, 
    lng: -122.4148, 
    expectedAttendees: 1200,
    category: "Community",
    description: "Neighborhood celebration with live music, local vendors, and community activities celebrating Mission culture.",
    time: "2024-12-22T14:00:00Z",
    location: "Mission District",
    similarEvents: [
      { id: "4a", title: "Castro Street Fair", lat: 37.7609, lng: -122.4350, category: "Community", time: "2024-12-23T13:00:00Z", expectedAttendees: 800 },
      { id: "4b", title: "Haight Street Fair", lat: 37.7693, lng: -122.4489, category: "Community", time: "2024-12-24T12:00:00Z", expectedAttendees: 950 },
      { id: "4c", title: "Chinatown Night Market", lat: 37.7941, lng: -122.4078, category: "Community", time: "2024-12-25T19:00:00Z", expectedAttendees: 1100 }
    ]
  },
  { 
    id: "5", 
    title: "North Beach Jazz Night", 
    lat: 37.8040, 
    lng: -122.4100, 
    expectedAttendees: 450,
    category: "Music",
    description: "Weekly jazz performances at various venues throughout North Beach, featuring both local and touring musicians.",
    time: "2024-12-19T20:00:00Z",
    location: "North Beach"
  },
  { 
    id: "6", 
    title: "Golden Gate Park Concert", 
    lat: 37.7694, 
    lng: -122.4862, 
    expectedAttendees: 5000,
    category: "Music",
    description: "Outdoor concert featuring indie rock bands with food trucks and local beer gardens.",
    time: "2024-12-21T15:00:00Z",
    location: "Golden Gate Park"
  },
  { 
    id: "7", 
    title: "Fisherman's Wharf Seafood Festival", 
    lat: 37.8080, 
    lng: -122.4177, 
    expectedAttendees: 3200,
    category: "Food & Drink",
    description: "Fresh seafood festival with local restaurants, cooking demonstrations, and live music.",
    time: "2024-12-16T11:00:00Z",
    location: "Fisherman's Wharf",
    similarEvents: [
      { id: "7a", title: "Crab Festival at Pier 39", lat: 37.8085, lng: -122.4098, category: "Food & Drink", time: "2024-12-17T12:00:00Z", expectedAttendees: 2100 }
    ]
  },
  { 
    id: "8", 
    title: "Tech Startup Pitch Night", 
    lat: 37.7849, 
    lng: -122.4094, 
    expectedAttendees: 280,
    category: "Business",
    description: "Monthly startup pitch competition with networking opportunities and investor panels.",
    time: "2024-12-19T18:30:00Z",
    location: "Financial District"
  },
  { 
    id: "9", 
    title: "Presidio Yoga in the Park", 
    lat: 37.7989, 
    lng: -122.4662, 
    expectedAttendees: 150,
    category: "Health & Wellness",
    description: "Morning yoga session with panoramic views of the Golden Gate Bridge.",
    time: "2024-12-16T08:00:00Z",
    location: "Presidio"
  },
  { 
    id: "10", 
    title: "Castro Theatre Film Festival", 
    lat: 37.7609, 
    lng: -122.4350, 
    expectedAttendees: 1400,
    category: "Entertainment",
    description: "Independent film festival showcasing local filmmakers and international cinema.",
    time: "2024-12-18T19:00:00Z",
    location: "Castro District",
    similarEvents: [
      { id: "10a", title: "Roxie Theater Documentary Night", lat: 37.7599, lng: -122.4148, category: "Entertainment", time: "2024-12-19T20:00:00Z", expectedAttendees: 120 }
    ]
  },
  { 
    id: "11", 
    title: "Lombard Street Art Fair", 
    lat: 37.8021, 
    lng: -122.4187, 
    expectedAttendees: 800,
    category: "Arts & Culture",
    description: "Local artists showcase paintings, sculptures, and handmade crafts on the world's crookedest street.",
    time: "2024-12-17T10:00:00Z",
    location: "Russian Hill"
  },
  { 
    id: "12", 
    title: "Chinatown Dragon Dance", 
    lat: 37.7941, 
    lng: -122.4078, 
    expectedAttendees: 2000,
    category: "Cultural",
    description: "Traditional dragon dance performance celebrating Chinese New Year with fireworks and festivities.",
    time: "2024-12-23T17:00:00Z",
    location: "Chinatown"
  },
  { 
    id: "13", 
    title: "Marina Green Kite Festival", 
    lat: 37.8049, 
    lng: -122.4426, 
    expectedAttendees: 1200,
    category: "Family",
    description: "Family-friendly kite flying festival with workshops, competitions, and food vendors.",
    time: "2024-12-21T11:00:00Z",
    location: "Marina District"
  },
  { 
    id: "14", 
    title: "Haight Street Vintage Market", 
    lat: 37.7693, 
    lng: -122.4489, 
    expectedAttendees: 900,
    category: "Shopping",
    description: "Vintage clothing, records, and antiques market in the heart of the historic Haight-Ashbury.",
    time: "2024-12-20T09:00:00Z",
    location: "Haight-Ashbury"
  },
  { 
    id: "15", 
    title: "Silicon Valley Tech Conference", 
    lat: 37.7849, 
    lng: -122.4094, 
    expectedAttendees: 4500,
    category: "Business",
    description: "Major tech conference featuring keynotes from industry leaders and networking sessions.",
    time: "2024-12-18T09:00:00Z",
    location: "Moscone Center",
    similarEvents: [
      { id: "15a", title: "AI Summit Downtown", lat: 37.7879, lng: -122.4074, category: "Business", time: "2024-12-19T09:00:00Z", expectedAttendees: 2200 },
      { id: "15b", title: "Blockchain Meetup", lat: 37.7849, lng: -122.4094, category: "Business", time: "2024-12-20T18:00:00Z", expectedAttendees: 350 }
    ]
  },
  { 
    id: "16", 
    title: "Sunset District Farmers Market", 
    lat: 37.7431, 
    lng: -122.4660, 
    expectedAttendees: 600,
    category: "Food & Drink",
    description: "Weekly farmers market featuring organic produce, artisanal breads, and local honey.",
    time: "2024-12-22T08:00:00Z",
    location: "Sunset District"
  },
  { 
    id: "17", 
    title: "Crissy Field Running Club", 
    lat: 37.8024, 
    lng: -122.4662, 
    expectedAttendees: 75,
    category: "Sports",
    description: "Weekly group run along the waterfront with views of Alcatraz and the Golden Gate Bridge.",
    time: "2024-12-17T07:00:00Z",
    location: "Crissy Field"
  },
  { 
    id: "18", 
    title: "Mission Dolores Park Picnic", 
    lat: 37.7596, 
    lng: -122.4269, 
    expectedAttendees: 300,
    category: "Community",
    description: "Community picnic with live acoustic music, local food vendors, and games for all ages.",
    time: "2024-12-21T12:00:00Z",
    location: "Mission Dolores Park"
  },
  { 
    id: "19", 
    title: "Nob Hill Wine Tasting", 
    lat: 37.7919, 
    lng: -122.4145, 
    expectedAttendees: 180,
    category: "Food & Drink",
    description: "Exclusive wine tasting featuring California vintages with cheese pairings and city views.",
    time: "2024-12-19T17:00:00Z",
    location: "Nob Hill"
  },
  { 
    id: "20", 
    title: "Pacific Heights Gallery Walk", 
    lat: 37.7886, 
    lng: -122.4324, 
    expectedAttendees: 420,
    category: "Arts & Culture",
    description: "Evening gallery walk through Pacific Heights featuring contemporary art and sculpture exhibitions.",
    time: "2024-12-20T18:00:00Z",
    location: "Pacific Heights"
  },
  { 
    id: "21", 
    title: "Alcatraz Night Tour", 
    lat: 37.8267, 
    lng: -122.4233, 
    expectedAttendees: 200,
    category: "Tourism",
    description: "Special after-dark tour of Alcatraz Island with exclusive access to restricted areas.",
    time: "2024-12-18T19:30:00Z",
    location: "Alcatraz Island"
  },
  { 
    id: "22", 
    title: "Richmond District Food Crawl", 
    lat: 37.7806, 
    lng: -122.4637, 
    expectedAttendees: 250,
    category: "Food & Drink",
    description: "Guided food tour through Richmond's diverse restaurants featuring Asian cuisine and local favorites.",
    time: "2024-12-22T11:00:00Z",
    location: "Richmond District"
  },
  { 
    id: "23", 
    title: "Embarcadero Bike Race", 
    lat: 37.7955, 
    lng: -122.3937, 
    expectedAttendees: 500,
    category: "Sports",
    description: "Competitive cycling race along the Embarcadero waterfront with amateur and professional categories.",
    time: "2024-12-17T08:00:00Z",
    location: "Embarcadero"
  },
  { 
    id: "24", 
    title: "Twin Peaks Sunrise Hike", 
    lat: 37.7544, 
    lng: -122.4477, 
    expectedAttendees: 85,
    category: "Outdoors",
    description: "Early morning hike to Twin Peaks for panoramic sunrise views over San Francisco.",
    time: "2024-12-16T06:30:00Z",
    location: "Twin Peaks"
  },
  { 
    id: "25", 
    title: "Japanese Tea Garden Ceremony", 
    lat: 37.7701, 
    lng: -122.4696, 
    expectedAttendees: 120,
    category: "Cultural",
    description: "Traditional Japanese tea ceremony demonstration with meditation and cultural education.",
    time: "2024-12-20T14:00:00Z",
    location: "Golden Gate Park"
  },
  { 
    id: "26", 
    title: "Outer Sunset Beach Bonfire", 
    lat: 37.7398, 
    lng: -122.5088, 
    expectedAttendees: 180,
    category: "Community",
    description: "Evening beach bonfire with s'mores, acoustic music, and ocean views at Ocean Beach.",
    time: "2024-12-21T18:00:00Z",
    location: "Ocean Beach"
  },
  { 
    id: "27", 
    title: "Financial District Food Truck Rally", 
    lat: 37.7849, 
    lng: -122.4094, 
    expectedAttendees: 1500,
    category: "Food & Drink",
    description: "Lunchtime food truck gathering featuring international cuisines and local favorites.",
    time: "2024-12-19T11:30:00Z",
    location: "Financial District"
  },
  { 
    id: "28", 
    title: "Bernal Heights Park Festival", 
    lat: 37.7420, 
    lng: -122.4156, 
    expectedAttendees: 700,
    category: "Community",
    description: "Neighborhood festival with live bands, local vendors, and activities for families.",
    time: "2024-12-22T13:00:00Z",
    location: "Bernal Heights"
  },
  { 
    id: "29", 
    title: "Coit Tower Photography Workshop", 
    lat: 37.8024, 
    lng: -122.4058, 
    expectedAttendees: 45,
    category: "Education",
    description: "Photography workshop focusing on urban landscape and architectural photography techniques.",
    time: "2024-12-17T14:00:00Z",
    location: "Telegraph Hill"
  },
  { 
    id: "30", 
    title: "Oracle Park Baseball Game", 
    lat: 37.7786, 
    lng: -122.3893, 
    expectedAttendees: 35000,
    category: "Sports",
    description: "San Francisco Giants home game with pre-game festivities and local food vendors.",
    time: "2024-12-23T13:05:00Z",
    location: "Oracle Park",
    similarEvents: [
      { id: "30a", title: "Chase Center Warriors Game", lat: 37.7680, lng: -122.3870, category: "Sports", time: "2024-12-24T19:30:00Z", expectedAttendees: 18000 }
    ]
  }
];

export const CONTROL_BUTTON_STYLES: React.CSSProperties = {
  padding: "8px 12px",
  background: "#111",
  color: "#fff",
  border: "1px solid #333",
  borderRadius: 8,
  cursor: "pointer"
};
