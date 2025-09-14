import { useState } from 'react';
import type { EventPoint } from '../types';
import { EventsAPI, type SimilaritySearchResponse, mapBackendEventToEventPoint } from '../services/api';

export function useSearch() {
	const [isSearchOpen, setIsSearchOpen] = useState(false);
	const [searchResults, setSearchResults] = useState<EventPoint[] | null>(null);
	const [isSearchActive, setIsSearchActive] = useState(false);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

	const openSearch = () => {
		setIsSearchOpen(true);
	};

    const closeSearch = () => {
        setIsSearchOpen(false);
    };

    // TODO: placeholderish method
    const executeSearch = async (query: string) => {
        try {
            const res: SimilaritySearchResponse = await EventsAPI.searchSimilarEvents({
                query_text: query,
                limit: 5, 
            });
            const results: EventPoint[] = res.similar_events.map(event => mapBackendEventToEventPoint(event as any));
            const hasResults = (res.total_found ?? results.length) > 0 && results.length > 0;
            const url = res.audio_response;
            setAudioUrl(url);
            setSearchResults(hasResults ? results : []);
            setIsSearchActive(hasResults);
            return { success: true, results } as const;
        } catch (err: any) {
            console.warn('Search failed', err);
            return { success: false, error: err?.message || 'Search failed' } as const;
        }
    };

	const clearSearch = () => {
		setSearchResults(null);
		setIsSearchActive(false);
	};

    return {
        isSearchOpen,
        searchResults,
        isSearchActive,
        openSearch,
        closeSearch,
        executeSearch,
        clearSearch,
        audioUrl
    };
}
