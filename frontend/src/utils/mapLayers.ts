// import type { Map as MLMap } from "maplibre-gl";
// import { findFirstSymbolLayerId } from './mapUtils';
// import { ensureCategoryPins } from '../components/Pin';

// export function setupMapLayers(map: MLMap) {
// 	setupHeatmapLayer(map);
// 	setupPinLayer(map);
// }
// 
// function setupHeatmapLayer(map: MLMap) {
// 	if (!map.getLayer("events-heat")) {
// 		map.addLayer(
// 			{
// 				id: "events-heat",
// 				type: "heatmap",
// 				source: "events",
// 				maxzoom: 18,
// 				paint: {
// 					// weight: use attendace (0..5000 -> 0..1)
// 					"heatmap-weight": [
// 						"interpolate",
// 						["linear"],
// 						["coalesce", ["to-number", ["get", "attendance"]], 0],
// 						0, 0,
// 						5000, 1
// 					],

// 					// intensity grows with zoom => crisper red cores when zoomed
// 					"heatmap-intensity": [
// 						"interpolate",
// 						["linear"],
// 						["zoom"],
// 						0, 0.6,
// 						9, 1.2,
// 						13, 1.8
// 					],

// 					// radius in pixels by zoom (tuned for city detail)
// 					"heatmap-radius": [
// 						"interpolate",
// 						["linear"],
// 						["zoom"],
// 						0, 2,
// 						7, 18,
// 						10, 28,
// 						13, 42,
// 						16, 64
// 					],

// 					// classic blue→cyan→yellow→orange→red
// 					"heatmap-color": [
// 						"interpolate",
// 						["linear"],
// 						["heatmap-density"],
// 						0.0, "rgba(0, 0, 255, 0.08)",
// 						0.10, "rgba(0, 180, 255, 0.6)",
// 						0.30, "rgba(0, 255, 150, 0.8)",
// 						0.55, "rgba(255, 255, 0, 0.95)",
// 						0.75, "rgba(255, 165, 0, 1.0)",
// 						1.0, "rgba(255, 0, 0, 1.0)"
// 					],

// 					// fade heatmap slightly at max zoom (optional)
// 					"heatmap-opacity": [
// 						"interpolate",
// 						["linear"],
// 						["zoom"],
// 						14, 0.95,
// 						18, 0.85
// 					]
// 				}
// 			},
// 			findFirstSymbolLayerId(map) || undefined
// 		);
// 	}
// }

// function setupPinLayer(map: MLMap) {
// 	// Use colored SVG pins per category
// 	try {
// 		if (!map.getLayer("events-pins")) {
// 			(map as any).addLayer({
// 				id: "events-pins",
// 				type: "symbol",
// 				source: "events",
// 				minzoom: 4,
// 				layout: {
// 					"icon-image": ["concat", "pin-", ["get", "category"]],
// 					"icon-size": [
// 						"interpolate",
// 						["linear"],
// 						["zoom"],
// 						12, 0.8,
// 						20, 1.3
// 					],
// 					"icon-allow-overlap": true,
// 					"icon-anchor": "bottom"
// 				}
// 			});
// 		}

// 		ensureCategoryPins(map);

// 		// listen for data changes to add icons for new categories
// 		const handlerKey = "__eventsPinsSeedHandler";
// 		if (!(map as any)[handlerKey]) {
// 			const onSourceData = (e: any) => {
// 				if (!e || e.sourceId !== "events") return;
// 				ensureCategoryPins(map);
// 			};
// 			(map as any)[handlerKey] = onSourceData;
// 			map.on("sourcedata", onSourceData);
// 		}
// 	} catch (e) {
// 		// no-op in non-browser environments
// 	}
// }
// function setupPinLayer(map: MLMap) {
	// 	// Use colored SVG pins per category
	// 	try {
	// 		if (!map.getLayer("events-pins")) {
	// 			(map as any).addLayer({
	// 				id: "events-pins",
	// 				type: "symbol",
	// 				source: "events",
	// 				minzoom: 4,
	// 				layout: {
	// 					"icon-image": ["concat", "pin-", ["get", "category"]],
	// 					"icon-size": [
	// 						"interpolate",
	// 						["linear"],
	// 						["zoom"],
	// 						12, 0.8,
	// 						20, 1.3
	// 					],
	// 					"icon-allow-overlap": true,
	// 					"icon-anchor": "bottom"
	// 				}
	// 			});
	// 		}
	
	// 		ensureCategoryPins(map);
	
	// 		// listen for data changes to add icons for new categories
	// 		const handlerKey = "__eventsPinsSeedHandler";
	// 		if (!(map as any)[handlerKey]) {
	// 			const onSourceData = (e: any) => {
	// 				if (!e || e.sourceId !== "events") return;
	// 				ensureCategoryPins(map);
	// 			};
	// 			(map as any)[handlerKey] = onSourceData;
	// 			map.on("sourcedata", onSourceData);
	// 		}
	// 	} catch (e) {
	// 		// no-op in non-browser environments
	// 	}
	// }


import type { Map as MLMap } from "maplibre-gl";
import { findFirstSymbolLayerId } from "./mapUtils";
import { ensureCategoryPins } from "../components/Pin";

export function setupMapLayers(map: MLMap) {
  if (!map.getSource("events")) return;
  setupHeatmapLayer(map);
  setupPinLayer(map);
}

function setupHeatmapLayer(map: MLMap) {
  const beforeId = findFirstSymbolLayerId(map) || undefined;

  if (!map.getLayer("events-heat-coarse")) {
    map.addLayer(
      {
        id: "events-heat-coarse",
        type: "heatmap",
        source: "events",
        maxzoom: 18,
        paint: {
          "heatmap-weight": [
            "let",
            "n",
            [
              "max",
              0,
              [
                "coalesce",
                ["to-number", ["get", "attendance"]],
                ["to-number", ["get", "attendees"]],
                0
              ]
            ],
            [
              "min",
              1,
              [
                "case",
                ["==", ["var", "n"], 0],
                0.06,
                [
                  "interpolate",
                  ["exponential", 0.6],
                  ["var", "n"],
                  1, 0.10,
                  50, 0.18,
                  100, 0.26,
                  300, 0.40,
                  1000, 0.62,
                  5000, 0.88
                ]
              ]
            ]
          ],
          "heatmap-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            0, 8,
            8, 28,
            12, 44,
            16, 70
          ],
          "heatmap-intensity": [
            "interpolate",
            ["linear"],
            ["zoom"],
            0, 0.8,
            10, 1.1,
            14, 1.3
          ],
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0.00, "rgba(0,0,0,0)",
            0.12, "rgba(0, 140, 255, 0.40)",
            0.35, "rgba(0, 255, 180, 0.70)",
            0.65, "rgba(255, 200, 0, 0.90)",
            1.00, "rgba(255, 80, 0, 1.00)"
          ],
          "heatmap-opacity": 0.85
        }
      },
      beforeId
    );
  }

  if (!map.getLayer("events-heat")) {
    map.addLayer(
      {
        id: "events-heat",
        type: "heatmap",
        source: "events",
        maxzoom: 18,
        paint: {
          "heatmap-weight": [
            "let",
            "n",
            [
              "max",
              0,
              [
                "coalesce",
                ["to-number", ["get", "attendance"]],
                ["to-number", ["get", "attendees"]],
                0
              ]
            ],
            [
              "min",
              1,
              [
                "case",
                ["==", ["var", "n"], 0],
                0.05,
                [
                  "interpolate",
                  ["exponential", 0.6],
                  ["var", "n"],
                  1, 0.10,
                  50, 0.20,
                  100, 0.28,
                  300, 0.42,
                  1000, 0.66,
                  5000, 0.90
                ]
              ]
            ]
          ],
          "heatmap-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            0, 2,
            8, 10,
            12, 18,
            16, 26
          ],
          "heatmap-intensity": [
            "interpolate",
            ["linear"],
            ["zoom"],
            0, 1.5,
            10, 3.0,
            14, 3.8
          ],
          "heatmap-color": [
            "interpolate",
            ["exponential", 3.0],
            ["heatmap-density"],
            0.00, "rgba(0,0,0,0)",
            0.05, "rgba(0, 180, 255, 0.60)",
            0.15, "rgba(0, 255, 180, 0.85)",
            0.35, "rgba(255, 240, 0, 1.00)",
            0.60, "rgba(255, 140, 0, 1.00)",
            0.85, "rgba(255, 0, 0, 1.00)"
          ],
          "heatmap-opacity": [
            "interpolate",
            ["linear"],
            ["zoom"],
            0, 0.0,
            6, 0.0,
            8, 0.9,
            18, 0.95
          ]
        }
      },
      beforeId
    );
  }
}

function setupPinLayer(map: MLMap) {
	try {
	  if (!map.getLayer("events-pins")) {
		(map as any).addLayer(
		  {
			id: "events-pins",
			type: "symbol",
			source: "events",
			minzoom: 4,
			layout: {
			  "icon-image": ["concat", "pin-", ["get", "category"]],
			  "icon-size": [
				"interpolate",
				["linear"],
				["zoom"],
				4, 0.70,
				8, 0.85,
				12, 1.05,
				20, 1.30
			  ],
			  "icon-anchor": "bottom",
			  "icon-allow-overlap": true,
  
			  // keep the icon glued to the map surface (not the screen)
			  "icon-pitch-alignment": "map",
			  "icon-rotation-alignment": "map",
  
			  // pull the art down so the stick/circle sits on the point.
			  // values tuned for your 64px viewBox + extra bottom padding,
			  // and for addImage(..., { pixelRatio: 2 }).
			  "icon-offset": [
				"interpolate",
				["linear"],
				["zoom"],
				4, ["literal", [0, -10]],
				8, ["literal", [0, -14]],
				12, ["literal", [0, -20]],
				16, ["literal", [0, -24]],
				20, ["literal", [0, -28]]
			  ]
			}
		  },
		  findFirstSymbolLayerId(map) || undefined
		);
	  }
  
	  ensureCategoryPins(map);
  
	  const handlerKey = "__eventsPinsSeedHandler";
	  if (!(map as any)[handlerKey]) {
		const onSourceData = (e: any) => {
		  if (!e || e.sourceId !== "events") return;
		  ensureCategoryPins(map);
		};
		(map as any)[handlerKey] = onSourceData;
		map.on("sourcedata", onSourceData);
	  }
	} catch {
	  // ignore in non-browser envs
	}
  }
  