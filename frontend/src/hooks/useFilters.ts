import { useCallback, useMemo, useState } from "react";
import { normalizeCategorySlug } from "../utils/categories";

export type FiltersState = {
  selectedCategories: string[]; // normalized slugs; empty -> no filtering
};

export function useFilters() {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  const isActive = selectedCategories.length > 0;

  const selectAll = useCallback(() => setSelectedCategories([]), []); // no-op here; set via setCategories from API
  const clearAll = useCallback(() => setSelectedCategories([]), []);

  const toggleCategory = useCallback((slug: string) => {
    const norm = normalizeCategorySlug(slug);
    if (!norm) return;
    setSelectedCategories((prev) => (prev.includes(norm) ? prev.filter((c) => c !== norm) : [...prev, norm]));
  }, []);

  const setMany = useCallback((slugs: string[]) => {
    setSelectedCategories(
      slugs
        .map((s) => normalizeCategorySlug(s))
        .filter((s): s is string => !!s)
    );
  }, []);

  const filteredCategories = useMemo(() => selectedCategories.slice(), [selectedCategories]);

  return {
    selectedCategories: filteredCategories,
    isActive,
    selectAll,
    clearAll,
    toggleCategory,
    setCategories: setMany,
  };
}


