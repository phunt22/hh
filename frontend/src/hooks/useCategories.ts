import { useEffect, useMemo, useState } from "react";
import { EventsAPI } from "../services/api";
import { normalizeCategorySlug, formatCategoryLabel } from "../utils/categories";

export function useCategories() {
  const [raw, setRaw] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    EventsAPI.getCategories()
      .then((cats) => {
        if (cancelled) return;
        setRaw(Array.isArray(cats) ? cats : []);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(String(e?.message || e || "Failed to load categories"));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

//   format and sort
  const categories = useMemo(() => {
    const norm = raw
      .map((c) => normalizeCategorySlug(c))
      .filter((c): c is string => !!c);
    const unique = Array.from(new Set(norm));
    return unique.sort((a, b) => formatCategoryLabel(a).localeCompare(formatCategoryLabel(b)));
  }, [raw]);

  return { categories, loading, error };
}


