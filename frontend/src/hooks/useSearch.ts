import { useState } from 'react';
import type { EventPoint } from '../types';
import { EventsAPI, type SimilaritySearchResponse, mapBackendEventToEventPoint } from '../services/api';

export function useSearch() {
	const [isSearchOpen, setIsSearchOpen] = useState(false);
	const [searchResults, setSearchResults] = useState<EventPoint[] | null>(null);
	const [isSearchActive, setIsSearchActive] = useState(false);

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
                limit: 25, // TODO probably too high?
                min_similarity: 0.6 // TODO tune this
            });
            const results: EventPoint[] = res.similar_events.map(se => mapBackendEventToEventPoint(se.event as any));
            setSearchResults(results);
            setIsSearchActive(true);
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
        clearSearch
    };
}
