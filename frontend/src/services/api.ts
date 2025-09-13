import type { EventPoint } from '../types';
import { normalizeCategorySlug } from '../utils/categories';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'https://fastapi-backend-e0m2.onrender.com/api/v1';


export interface BackendEvent {
  id: string;
  title: string;
  description?: string;
  category: string;
  longitude?: number;
  latitude?: number;
  start?: string;
  end?: string;
  location?: string;
  attendance?: number;
  created_at: string;
  updated_at: string;
  related_event_ids?: string;
}

export interface SimilaritySearchRequest {
  query_text?: string;
  event_id?: string;
  limit?: number;
  min_similarity?: number;
  include_related?: boolean;
}

export interface SimilarEvent {
  event: BackendEvent;
  similarity_score: number;
  relationship_type: string;
}

export interface SimilaritySearchResponse {
  query_event?: BackendEvent;
  similar_events: SimilarEvent[];
  total_found: number;
}

// TODO: remove this when api supports attendace | placeholder
// function getDefaultAttendanceFromId(id: string): number {
//   let hash = 0;
//   for (let i = 0; i < id.length; i++) {
//     hash = ((hash << 5) - hash + id.charCodeAt(i)) | 0;
//   }
//   const min = 50;
//   const max = 1000;
//   const range = max - min + 1;
//   const positive = Math.abs(hash);
//   return min + (positive % range);
// }

export function mapBackendEventToEventPoint(backendEvent: BackendEvent): EventPoint {
  // TODO: change this line to just be attendance when API is ready
  const attendance = backendEvent.attendance
  
  // typeof backendEvent.attendance === 'number' ? backendEvent.attendance : getDefaultAttendanceFromId(backendEvent.id);
  return {
    id: backendEvent.id,
    title: backendEvent.title,
    lat: backendEvent.latitude || 0,
    lng: backendEvent.longitude || 0,
    description: backendEvent.description,
    attendance: attendance,
    start: backendEvent.start,
    end: backendEvent.end,
    category: normalizeCategorySlug(backendEvent.category) || '',
    location: backendEvent.location,
  };
}

export class EventsAPI {
  // originally a debug method, can probably be safely removed
  // static async getEventsRaw(params: {
  //   limit?: number;
  //   skip?: number;
  //   category?: string;
  //   location_query?: string;
  //   lat?: number;
  //   lng?: number;
  //   radius_km?: number;
  // } = {}): Promise<BackendEvent[]> {
  //   const queryParams = new URLSearchParams();

  //   Object.entries(params).forEach(([key, value]) => {
  //     if (value !== undefined) {
  //       queryParams.append(key, value.toString());
  //     }
  //   });

  //   const response = await fetch(`${API_BASE_URL}/events/?${queryParams}`);

  //   if (!response.ok) {
  //     throw new Error(`Failed to fetch events: ${response.statusText}`);
  //   }

  //   return response.json();
  // }

  static async getEvents(params: {
    limit?: number;
    skip?: number;
    category?: string;
    location_query?: string;
    lat?: number;
    lng?: number;
    radius_km?: number;
    attendance?: number;
  } = {}): Promise<EventPoint[]> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value.toString());
      }
    });
    
    const response = await fetch(`${API_BASE_URL}/events/?${queryParams}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch events: ${response.statusText}`);
    }
    
    const backendEvents: BackendEvent[] = await response.json();
    return backendEvents.map(mapBackendEventToEventPoint);
  }

  static async getEvent(eventId: string): Promise<EventPoint> {
    const response = await fetch(`${API_BASE_URL}/events/${eventId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch event: ${response.statusText}`);
    }
    
    const backendEvent: BackendEvent = await response.json();
    return mapBackendEventToEventPoint(backendEvent);
  }

  static async searchSimilarEvents(request: SimilaritySearchRequest): Promise<SimilaritySearchResponse> {
    const response = await fetch(`${API_BASE_URL}/events/search/similar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const txt = await response.text().catch(() => '');
      throw new Error(`Failed to search similar events: ${response.status} ${response.statusText}${txt ? ` - ${txt}` : ''}`);
    }
    
    return response.json();
  }

  static async getSimilarEvents(
    eventId: string,
    params: {
      limit?: number;
      min_similarity?: number;
      include_related?: boolean;
    } = {}
  ): Promise<SimilaritySearchResponse> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value.toString());
      }
    });
    
    const response = await fetch(`${API_BASE_URL}/events/${eventId}/similar?${queryParams}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch similar events: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Viewport-based query for the map
  static async getEventsInViewport(
    center: { lat: number; lng: number },
    radiusKm: number,
    limit: number = 100
  ): Promise<EventPoint[]> {
    return this.getEvents({
      lat: center.lat,
      lng: center.lng,
      radius_km: radiusKm,
      limit,
    });
  }

  static async getCategories(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/events/categories/list`);
    if (!response.ok) {
      throw new Error(`Failed to fetch categories: ${response.statusText}`);
    }
    const categories: string[] = await response.json();
    return categories;
  }
}
