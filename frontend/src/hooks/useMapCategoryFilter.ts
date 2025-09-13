import { useEffect } from "react";
import type { Map as MLMap } from "maplibre-gl";

export function useMapCategoryFilter(map: MLMap | null, categories: string[]) {
  useEffect(() => {
    if (!map) return;

    const apply = () => {
      const layerIds = ["events-heat", "events-pins"];
      if (!categories || categories.length === 0) {
        for (const id of layerIds) {
          if (map.getLayer(id)) {
            (map as any).setFilter(id, null);
          }
        }
        return;
      }

      const filterExpr: any = [
        "all",
        ["in", ["get", "category"], ["literal", categories]],
      ];

      for (const id of layerIds) {
        if (map.getLayer(id)) {
          (map as any).setFilter(id, filterExpr);
        }
      }
    };

    if ((map as any).isStyleLoaded && (map as any).isStyleLoaded()) {
      apply();
    } else {
      const onLoad = () => apply();
      map.once("load", onLoad);
      return () => {
        map.off("load", onLoad);
      };
    }
  }, [map, categories]);
}


