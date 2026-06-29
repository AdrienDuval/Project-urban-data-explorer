"use client";

import type { Feature, FeatureCollection, Geometry } from "geojson";
import { useEffect, useMemo, useRef, useState } from "react";
import Map, {
  Layer,
  NavigationControl,
  Popup,
  Source,
  type LayerProps,
  type MapMouseEvent,
  type MapRef,
  type ViewState,
} from "react-map-gl/mapbox";

import {
  fetchBdcomByIris,
  fetchDvfByIris,
  fetchRentMap,
  fetchSaleMap,
  fetchSaleTimeline,
  fetchThermalComfortMap,
  fetchTransportPoints,
  fetchVivabiliteArrondissement,
  fetchVivabiliteMap,
  fetchDemographicsMap,
  getAnalyticsUserKey,
  recordZoneClick,
} from "@/lib/api";
import type {
  BdcomIrisStats,
  DvfIrisStats,
  IndicatorMapFeatureCollection,
  IndicatorMapProperties,
  SaleTimelineFeatureCollection,
  TransportPoint,
  TransportPointFeatureCollection,
  TransportPointProperties,
  TransportType,
  VivabiliteFeatureCollection,
} from "@/types/map";
import { LanguageProvider, useI18n } from "@/lib/i18n";

type WeightKey =
  | "school_score"
  | "childcare_score"
  | "safety_score"
  | "healthcare_score"
  | "environment_score"
  | "transport_score"
  | "daily_services_score"
  | "green_spaces_score";

type MainIndicator = "vivabilite" | "transport" | "thermal" | "housing" | "demographics";

type MetricKey =
  | "vivabilite_score"
  | "essential_connectivity_score"
  | "family_mix"
  | WeightKey
  | "thermal_score"
  | "tree_density_score"
  | "cooling_area_score"
  | "rent_score"
  | "sale_score"
  | "score_revenus"
  | "proximity_score";

type Weights = Record<WeightKey, number>;

type ComputedProperties = IndicatorMapProperties & {
  map_id: string;
  weighted_score: number | null;
  weighted_rank: number | null;
  score_delta: number | null;
  score_percentile: number | null;
  active_score: number | null;
  active_rank: number | null;
  active_percentile: number | null;
};

type ComputedFeature = Feature<Geometry, ComputedProperties>;
type ComputedFeatureCollection = FeatureCollection<Geometry, ComputedProperties>;

type InteractiveMapEvent = MapMouseEvent & {
  features?: Array<{ layer?: { id?: string }; properties?: unknown }>;
};

const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
const detailedFallbackMapStyle = {
  version: 8 as const,
  sources: {
    osm: {
      type: "raster" as const,
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster" as const, source: "osm" }],
};
const mapStyle =
  process.env.NEXT_PUBLIC_MAP_STYLE_URL ??
  (mapboxToken
    ? "mapbox://styles/mapbox/outdoors-v12"
    : detailedFallbackMapStyle);

const ZOOM_BREAK = 11; // below this zoom → arrondissement layer; at or above → IRIS layer

const initialViewState: Partial<ViewState> = {
  longitude: 2.3522,
  latitude: 48.8566,
  zoom: 11.45,
  pitch: 0,
  bearing: 0,
};

const ileDeFranceMaxBounds: [[number, number], [number, number]] = [
  [1.4, 48.1],
  [3.6, 49.3],
];

const defaultWeights: Weights = {
  school_score: 20,
  childcare_score: 15,
  safety_score: 20,
  healthcare_score: 15,
  environment_score: 15,
  transport_score: 5,
  daily_services_score: 2.5,
  green_spaces_score: 7.5,
};

const equalWeights: Weights = {
  school_score: 12.5,
  childcare_score: 12.5,
  safety_score: 12.5,
  healthcare_score: 12.5,
  environment_score: 12.5,
  transport_score: 12.5,
  daily_services_score: 12.5,
  green_spaces_score: 12.5,
};

const PILLAR_META_BASE: Array<{
  key: WeightKey;
  labelKey: string;
  shortKey: string;
  descKey: string;
  color: string;
}> = [
  { key: "school_score", labelKey: "pillar.school.label", shortKey: "pillar.school.short", descKey: "pillar.school.desc", color: "#2563eb" },
  { key: "childcare_score", labelKey: "pillar.childcare.label", shortKey: "pillar.childcare.short", descKey: "pillar.childcare.desc", color: "#db2777" },
  { key: "safety_score", labelKey: "pillar.safety.label", shortKey: "pillar.safety.short", descKey: "pillar.safety.desc", color: "#dc2626" },
  { key: "healthcare_score", labelKey: "pillar.healthcare.label", shortKey: "pillar.healthcare.short", descKey: "pillar.healthcare.desc", color: "#0891b2" },
  { key: "environment_score", labelKey: "pillar.environment.label", shortKey: "pillar.environment.short", descKey: "pillar.environment.desc", color: "#65a30d" },
  { key: "transport_score", labelKey: "pillar.transport.label", shortKey: "pillar.transport.short", descKey: "pillar.transport.desc", color: "#7c3aed" },
  { key: "daily_services_score", labelKey: "pillar.services.label", shortKey: "pillar.services.short", descKey: "pillar.services.desc", color: "#ea580c" },
  { key: "green_spaces_score", labelKey: "pillar.green.label", shortKey: "pillar.green.short", descKey: "pillar.green.desc", color: "#16a34a" },
];

type PillarMetaItem = {
  key: WeightKey;
  label: string;
  shortLabel: string;
  description: string;
  color: string;
};

function usePillarMeta(): PillarMetaItem[] {
  const { t } = useI18n();
  return useMemo(
    () =>
      PILLAR_META_BASE.map((p) => ({
        key: p.key,
        label: t(p.labelKey),
        shortLabel: t(p.shortKey),
        description: t(p.descKey),
        color: p.color,
      })),
    [t],
  );
}

const transportTypes: Array<{
  type: TransportType;
  label: string;
  icon: string;
  color: string;
}> = [
  { type: "metro", label: "Métro", icon: "M", color: "#0055a4" },
  { type: "rail", label: "RER / Rail", icon: "R", color: "#e30613" },
  { type: "tram", label: "Tram", icon: "T", color: "#6f2da8" },
  { type: "bus", label: "Bus", icon: "BUS", color: "#00a88f" },
  { type: "velib", label: "Vélib", icon: "V", color: "#86bd24" },
];

const MAIN_INDICATOR_BASE: Array<{
  key: MainIndicator;
  labelKey: string;
  descKey: string;
  abbr: string;
}> = [
  { key: "vivabilite", labelKey: "main.vivabilite.label", descKey: "main.vivabilite.desc", abbr: "VF" },
  { key: "transport", labelKey: "main.transport.label", descKey: "main.transport.desc", abbr: "TR" },
  { key: "thermal", labelKey: "main.thermal.label", descKey: "main.thermal.desc", abbr: "TH" },
  { key: "housing", labelKey: "main.housing.label", descKey: "main.housing.desc", abbr: "LG" },
  { key: "demographics", labelKey: "main.demographics.label", descKey: "main.demographics.desc", abbr: "DM" },
];

type MainIndicatorOption = {
  key: MainIndicator;
  label: string;
  description: string;
  abbr: string;
};

function useMainIndicatorOptions(): MainIndicatorOption[] {
  const { t } = useI18n();
  return useMemo(
    () =>
      MAIN_INDICATOR_BASE.map((m) => ({
        key: m.key,
        label: t(m.labelKey),
        description: t(m.descKey),
        abbr: m.abbr,
      })),
    [t],
  );
}

function MainIndicatorGlyph({ indicator }: { indicator: MainIndicator }) {
  const stroke = "currentColor";
  const line = {
    fill: "none" as const,
    stroke,
    strokeWidth: 1.35,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  switch (indicator) {
    case "vivabilite":
      return (
        <svg aria-hidden className="h-4 w-4" viewBox="0 0 16 16">
          <circle cx="8" cy="6.5" fill="none" r="2.25" stroke={stroke} strokeWidth={1.35} />
          <path d="M8 2v1.25M5.2 4.2l.9.9M10.9 5.1l.9-.9M4 8.5h8M6 13h4" {...line} />
        </svg>
      );
    case "transport":
      return (
        <svg aria-hidden className="h-4 w-4" viewBox="0 0 16 16">
          <path d="M4 12V6l4-3 4 3v6M4 10h8M6 12v2M10 12v2" {...line} />
        </svg>
      );
    case "thermal":
      return (
        <svg aria-hidden className="h-4 w-4" viewBox="0 0 16 16">
          <path d="M8 2v8.5a2.5 2.5 0 1 0 2.5-2.5M8 4.5V2" {...line} />
        </svg>
      );
    case "housing":
      return (
        <svg aria-hidden className="h-4 w-4" viewBox="0 0 16 16">
          <path d="M2 7l6-4.5L14 7v7H2V7zM6 14V9h4v5" {...line} />
        </svg>
      );
    case "demographics":
      return (
        <svg aria-hidden className="h-4 w-4" viewBox="0 0 16 16">
          <circle cx="5" cy="5" r="2" fill="none" stroke={stroke} strokeWidth={1.35} />
          <circle cx="11" cy="5" r="2" fill="none" stroke={stroke} strokeWidth={1.35} />
          <path d="M1 13c0-2.2 1.8-4 4-4s4 1.8 4 4M9 9c1-.6 2.2-.8 3 0 1.5.8 2.5 2.2 3 4" {...line} />
        </svg>
      );
    default:
      return null;
  }
}

type SubMetricOption = { key: MetricKey; label: string; description: string };

function useSubMetricOptions(): Record<MainIndicator, SubMetricOption[]> {
  const { t } = useI18n();
  const pillarMeta = usePillarMeta();
  return useMemo(
    () => ({
      vivabilite: [
        { key: "vivabilite_score", label: t("sub.official.label"), description: t("sub.official.desc") },
        { key: "essential_connectivity_score", label: t("sub.connectivity.label"), description: t("sub.connectivity.desc") },
        { key: "family_mix", label: t("sub.familymix.label"), description: t("sub.familymix.desc") },
        ...pillarMeta.map((pillar) => ({
          key: pillar.key,
          label: pillar.label,
          description: pillar.description,
        })),
      ],
      transport: [
        { key: "transport_score", label: t("sub.accessibility.label"), description: t("sub.accessibility.desc") },
      ],
      thermal: [
        { key: "thermal_score", label: t("sub.thermal.label"), description: t("sub.thermal.desc") },
        { key: "tree_density_score", label: t("sub.treedensity.label"), description: t("sub.treedensity.desc") },
        { key: "cooling_area_score", label: t("sub.cooling.label"), description: t("sub.cooling.desc") },
        { key: "proximity_score", label: t("sub.proximity.label"), description: t("sub.proximity.desc") },
      ],
      housing: [
        { key: "rent_score", label: t("sub.rent.label"), description: t("sub.rent.desc") },
        { key: "sale_score", label: t("sub.sale.label"), description: t("sub.sale.desc") },
      ],
      demographics: [
        { key: "score_revenus", label: t("sub.revenus.label"), description: t("sub.revenus.desc") },
      ],
    }),
    [t, pillarMeta],
  );
}

function useMetricMeta(): Record<MetricKey, { label: string; description: string }> {
  const subMetricOptions = useSubMetricOptions();
  return useMemo(
    () =>
      Object.values(subMetricOptions)
        .flat()
        .reduce(
          (meta, option) => {
            meta[option.key] = option;
            return meta;
          },
          {} as Record<MetricKey, { label: string; description: string }>,
        ),
    [subMetricOptions],
  );
}

const fillLayer: LayerProps = {
  id: "vivabilite-fill",
  type: "fill",
  paint: {
    // coalesce falls back to -1 when active_score is null/missing;
    // the -1 stop renders gray so excluded zones look distinct
    "fill-color": [
      "interpolate",
      ["linear"],
      ["coalesce", ["to-number", ["get", "active_score"], -1], -1],
      -1, "#e2e8f0",
      0, "#f43f5e",
      2, "#fb923c",
      4, "#fbbf24",
      6, "#a3e635",
      8, "#22c55e",
      10, "#047857",
    ],
    "fill-opacity": [
      "interpolate",
      ["linear"],
      ["coalesce", ["to-number", ["get", "active_score"], -1], -1],
      -1, 0.28,
      0, 0.68,
      10, 0.78,
    ],
    "fill-outline-color": "rgba(15, 23, 42, 0.18)",
  },
};

const outlineLayer: LayerProps = {
  id: "vivabilite-outline",
  type: "line",
  paint: {
    "line-color": "rgba(15, 23, 42, 0.22)",
    "line-width": ["interpolate", ["linear"], ["zoom"], 10, 0.35, 14, 1],
  },
};

const transportClusterLayer: LayerProps = {
  id: "transport-clusters",
  type: "circle",
  filter: ["has", "point_count"],
  paint: {
    "circle-color": "#111827",
    "circle-opacity": 0.88,
    "circle-radius": ["step", ["get", "point_count"], 18, 25, 24, 100, 32],
    "circle-stroke-color": "#ffffff",
    "circle-stroke-width": 2,
  },
};

const transportClusterCountLayer: LayerProps = {
  id: "transport-cluster-count",
  type: "symbol",
  filter: ["has", "point_count"],
  layout: {
    "text-field": ["get", "point_count_abbreviated"],
    "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
    "text-size": 12,
  },
  paint: {
    "text-color": "#ffffff",
  },
};

const transportPointCircleLayer: LayerProps = {
  id: "transport-points",
  type: "circle",
  filter: ["!", ["has", "point_count"]],
  paint: {
    "circle-color": [
      "match",
      ["get", "type"],
      "metro",
      "#0055a4",
      "rail",
      "#e30613",
      "tram",
      "#6f2da8",
      "bus",
      "#00a88f",
      "velib",
      "#86bd24",
      "#111827",
    ],
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 10.5, 5, 14, 9],
    "circle-stroke-color": "#ffffff",
    "circle-stroke-width": 1.5,
  },
};

const transportPointLabelLayer: LayerProps = {
  id: "transport-point-labels",
  type: "symbol",
  filter: ["!", ["has", "point_count"]],
  layout: {
    "text-field": ["get", "icon_label"],
    "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
    "text-size": ["interpolate", ["linear"], ["zoom"], 10.5, 8, 14, 10],
    "text-allow-overlap": true,
    "text-ignore-placement": true,
  },
  paint: {
    "text-color": "#ffffff",
  },
};

function formatScore(value: number | null | undefined) {
  return typeof value === "number" ? `${value.toFixed(1)}/10` : "No data";
}

function formatNumber(value: number | null | undefined) {
  return typeof value === "number" ? Intl.NumberFormat("fr-FR").format(value) : "N/A";
}

/** Bounding box [[minLng,minLat],[maxLng,maxLat]] of any GeoJSON geometry, or null. */
function geometryBounds(
  geometry: Geometry,
): [[number, number], [number, number]] | null {
  let minLng = Infinity;
  let minLat = Infinity;
  let maxLng = -Infinity;
  let maxLat = -Infinity;

  const visit = (coords: unknown): void => {
    if (Array.isArray(coords) && typeof coords[0] === "number") {
      const [lng, lat] = coords as [number, number];
      minLng = Math.min(minLng, lng);
      minLat = Math.min(minLat, lat);
      maxLng = Math.max(maxLng, lng);
      maxLat = Math.max(maxLat, lat);
      return;
    }
    if (Array.isArray(coords)) coords.forEach(visit);
  };

  if (!("coordinates" in geometry)) return null;
  visit(geometry.coordinates);
  if (!Number.isFinite(minLng) || !Number.isFinite(minLat)) return null;
  return [
    [minLng, minLat],
    [maxLng, maxLat],
  ];
}

/** "2025-10-01" → "T4 2025" for the timeline label. */
function formatQuarterLabel(period: string | null | undefined) {
  if (!period) return "";
  const [year, month] = period.split("-");
  const quarter = { "01": "T1", "04": "T2", "07": "T3", "10": "T4" }[month] ?? "";
  return `${quarter} ${year}`.trim();
}

/** Short explanations for metric tiles (sidebar + detail panel). */
const UI_HINTS = {
  zones:
    "Number of zones still shown after search, arrondissement filter, and minimum score. IRIS units at detailed zoom; arrondissement polygons when zoomed out.",
  sidebarAvg:
    "Mean of the headline score (0–10) over all visible zones. Each zone counts equally (not weighted by population).",
  schoolsWeight:
    "Share of the Schools pillar in your slider weights (family livability). This is not the proportion of schools in Paris.",
  dynamicRank:
    "Rank by the headline score among zones in the current view only (after filters). 1 is the best visible zone.",
  percentile:
    "How this zone compares to other visible zones on the headline score after filters. Higher is better; top zone in the list is 100%.",
  delta:
    "Headline score minus the stored vivabilité composite from the pipeline. On a single pillar, headline is that pillar, so you see how it differs from the overall score.",
  originalScore:
    "Fixed overall family livability from the data pipeline (standard composite). Compare to the headline when you use Custom mix or another sub-indicator.",
  avgCompare:
    "Mean headline score across all visible zones, the same value as Avg in the sidebar.",
  pillarStrong:
    "Pillar with the highest 0–10 score for this zone among schools, transport, services, green space, and healthcare.",
  pillarWeak:
    "Pillar with the lowest 0–10 score for this zone among the five livability themes.",
} as const;

function MetricHint({ text, labelForA11y }: { text: string; labelForA11y: string }) {
  const { t } = useI18n();
  return (
    <span className="group/hint relative ml-0.5 inline-flex shrink-0 align-middle">
      <button
        aria-label={`${t("a11y.about")} ${labelForA11y}`}
        className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-current/35 text-[9px] font-bold leading-none opacity-65 hover:opacity-100 focus:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#007AFF]/50"
        title={text}
        type="button"
      >
        ?
      </button>
      <span
        className="invisible absolute left-0 top-full z-[70] mt-1.5 w-[min(272px,calc(100vw-2.5rem))] rounded-lg border border-slate-200/90 bg-white px-2.5 py-2 text-left text-[10px] font-normal normal-case leading-snug tracking-normal text-slate-700 shadow-xl opacity-0 transition-opacity duration-150 group-hover/hint:visible group-hover/hint:opacity-100 group-focus-within/hint:visible group-focus-within/hint:opacity-100"
        role="tooltip"
      >
        {text}
      </span>
    </span>
  );
}

function clampWeight(value: number) {
  return Math.max(0, Math.min(100, value));
}

function effectiveWeight(weights: Weights, key: WeightKey) {
  const total = Object.values(weights).reduce((sum, weight) => sum + weight, 0);
  return total > 0 ? weights[key] / total : 0;
}

function calculateWeightedScore(properties: IndicatorMapProperties, weights: Weights) {
  let weightedSum = 0;
  let availableWeight = 0;

  for (const pillar of PILLAR_META_BASE) {
    const value = properties[pillar.key];
    const weight = weights[pillar.key];

    if (typeof value === "number" && weight > 0) {
      weightedSum += value * weight;
      availableWeight += weight;
    }
  }

  if (availableWeight === 0) {
    return null;
  }

  return Number((weightedSum / availableWeight).toFixed(2));
}

function scoreForMetric(
  properties: IndicatorMapProperties,
  weightedScore: number | null,
  metric: MetricKey,
) {
  if (metric === "family_mix") {
    return weightedScore;
  }

  const value = properties[metric as keyof IndicatorMapProperties];
  return typeof value === "number" ? value : null;
}

function mapFeatureId(properties: IndicatorMapProperties) {
  return (
    properties.map_id ??
    properties.code_iris ??
    properties.code_arrondissement ??
    properties.name ??
    ""
  ).toString();
}

function getTransportMeta(type: string) {
  return transportTypes.find((item) => item.type === type) ?? transportTypes[0];
}

function buildTransportGeojson(
  points: TransportPoint[],
  visibleTypes: Record<TransportType, boolean>,
): TransportPointFeatureCollection {
  return {
    type: "FeatureCollection",
    features: points
      .filter((point) => visibleTypes[point.type])
      .map((point) => {
        const meta = getTransportMeta(point.type);

        return {
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [point.lng, point.lat],
          },
          properties: {
            ...point,
            icon_label: meta.icon,
            display_type: meta.label,
          },
        };
      }),
  };
}

function getFeatureProperties(event: InteractiveMapEvent) {
  return event.features?.[0]?.properties as ComputedProperties | undefined;
}

function getTransportProperties(event: InteractiveMapEvent) {
  return event.features?.[0]?.properties as TransportPointProperties | undefined;
}

function buildComputedGeojson(
  data: IndicatorMapFeatureCollection | VivabiliteFeatureCollection | null,
  weights: Weights,
  metric: MetricKey,
): ComputedFeatureCollection | null {
  if (!data) {
    return null;
  }

  const features: ComputedFeature[] = data.features.map((feature) => {
    const weightedScore = calculateWeightedScore(feature.properties, weights);
    const activeScore = scoreForMetric(feature.properties, weightedScore, metric);

    return {
      ...feature,
      properties: {
        ...feature.properties,
        map_id: mapFeatureId(feature.properties),
        weighted_score: weightedScore,
        weighted_rank: null,
        score_delta:
          typeof activeScore === "number" &&
          typeof feature.properties.vivabilite_score === "number"
            ? Number((activeScore - feature.properties.vivabilite_score).toFixed(2))
            : null,
        score_percentile: null,
        active_score: activeScore,
        active_rank: null,
        active_percentile: null,
      },
    };
  });

  const weightedRanked = [...features]
    .filter((feature) => typeof feature.properties.weighted_score === "number")
    .sort(
      (a, b) =>
        (b.properties.weighted_score ?? -1) - (a.properties.weighted_score ?? -1),
    );

  weightedRanked.forEach((feature, index) => {
    feature.properties.weighted_rank = index + 1;
    feature.properties.score_percentile = Number(
      (((weightedRanked.length - index) / weightedRanked.length) * 100).toFixed(0),
    );
  });

  const activeRanked = [...features]
    .filter((feature) => typeof feature.properties.active_score === "number")
    .sort(
      (a, b) =>
        (b.properties.active_score ?? -1) - (a.properties.active_score ?? -1),
    );

  activeRanked.forEach((feature, index) => {
    feature.properties.active_rank = index + 1;
    feature.properties.active_percentile = Number(
      (((activeRanked.length - index) / activeRanked.length) * 100).toFixed(0),
    );
  });

  return { type: "FeatureCollection", features };
}

function filterComputedGeojson(
  data: ComputedFeatureCollection | null,
  query: string,
  arrondissementFilter: string,
  minScore: number,
): ComputedFeatureCollection | null {
  if (!data) {
    return null;
  }

  const normalizedQuery = query.trim().toLowerCase();
  const features = data.features
    .filter((feature) => {
      const properties = feature.properties;
      const searchText = [
        properties.name,
        properties.arrondissement,
        properties.code_iris,
        properties.code_arrondissement,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return (
        (!normalizedQuery || searchText.includes(normalizedQuery)) &&
        (!arrondissementFilter || properties.arrondissement === arrondissementFilter) &&
        (typeof properties.active_score !== "number" || properties.active_score >= minScore)
      );
    })
    .sort(
      (a, b) =>
        (b.properties.active_score ?? -1) - (a.properties.active_score ?? -1),
    )
    .map((feature, index, all) => ({
      ...feature,
      properties: {
        ...feature.properties,
        active_rank: typeof feature.properties.active_score === "number" ? index + 1 : null,
        active_percentile:
          typeof feature.properties.active_score === "number"
            ? Number((((all.length - index) / all.length) * 100).toFixed(0))
            : null,
      },
    }));

  return { type: "FeatureCollection", features };
}

function GlassCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`border border-white/65 bg-white/82 shadow-[0_10px_40px_rgba(15,23,42,0.08)] ring-1 ring-slate-900/5 backdrop-blur-xl ${className}`}
    >
      {children}
    </div>
  );
}

function Metric({
  label,
  value,
  tone = "light",
  hint,
}: {
  label: string;
  value: string;
  tone?: "light" | "dark" | "green";
  hint?: string;
}) {
  const styles = {
    light: "bg-white/70 text-slate-950",
    dark: "bg-slate-950 text-white shadow-[0_2px_10px_rgba(15,23,42,0.18)]",
    green: "bg-emerald-600 text-white",
  };

  return (
    <div className={`rounded-xl px-2 py-1.5 ${styles[tone]}`}>
      <p className="flex items-center gap-0.5 text-[9px] font-medium uppercase tracking-wide opacity-75">
        <span className="min-w-0 truncate">{label}</span>
        {hint ? <MetricHint labelForA11y={label} text={hint} /> : null}
      </p>
      <p className="mt-0.5 text-[15px] font-semibold leading-tight tracking-tight tabular-nums">
        {value}
      </p>
    </div>
  );
}

function SidebarExpandedContent({
  featureCount,
  averageScore,
  schoolShare,
  loadingStates,
  mainIndicator,
  selectedSubMetric,
  transportTypeCounts,
  visibleTransportTypes,
  arrondissementOptions,
  arrondissementFilter,
  minScore,
  query,
  ranking,
  selectedMapId,
  onSubMetricChange,
  onArrondissementFilterChange,
  onMinScoreChange,
  onQueryChange,
  onRankingSelect,
  onTransportTypeToggle,
}: {
  featureCount: number;
  averageScore: number | null;
  schoolShare: number;
  loadingStates: Record<MainIndicator, boolean>;
  mainIndicator: MainIndicator;
  selectedSubMetric: MetricKey;
  transportTypeCounts: Record<TransportType, number>;
  visibleTransportTypes: Record<TransportType, boolean>;
  arrondissementOptions: string[];
  arrondissementFilter: string;
  minScore: number;
  query: string;
  ranking: ComputedFeature[];
  selectedMapId: string | null;
  onSubMetricChange: (metric: MetricKey) => void;
  onArrondissementFilterChange: (arrondissement: string) => void;
  onMinScoreChange: (score: number) => void;
  onQueryChange: (query: string) => void;
  onRankingSelect: (id: string) => void;
  onTransportTypeToggle: (type: TransportType) => void;
}) {
  const { t } = useI18n();
  const subMetricOptions = useSubMetricOptions();
  const showTransportFilters = mainIndicator === "transport";
  const subMetrics = subMetricOptions[mainIndicator];

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto overscroll-contain border-l border-slate-900/8 bg-white/80 backdrop-blur-xl">
      <div className="flex shrink-0 items-center justify-between border-b border-slate-900/8 px-3 py-2.5">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
            {t("sidebar.urbanData")}
          </p>
          <h1 className="text-base font-semibold tracking-tight text-slate-950">{t("sidebar.explorer")}</h1>
        </div>
        <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-[10px] font-semibold text-[#007AFF] ring-1 ring-[#007AFF]/20">
          Paris
        </span>
      </div>

      <div className="space-y-1.5 px-3 pb-3 pt-3">
        <p className="px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          {t("sidebar.subIndicators")}
        </p>
        {subMetrics.map((metric) => {
          const active = selectedSubMetric === metric.key;
          return (
            <button
              className={`w-full rounded-xl px-2.5 py-2 text-left transition ${
                active
                  ? "bg-slate-900 text-white shadow-[0_2px_10px_rgba(15,23,42,0.18)]"
                  : "bg-white/70 text-slate-600 hover:bg-white"
              }`}
              key={metric.key}
              onClick={() => onSubMetricChange(metric.key)}
              type="button"
            >
              <span className="block text-[13px] font-semibold leading-snug">{metric.label}</span>
              <span
                className={`mt-0.5 block line-clamp-2 text-[11px] leading-snug ${
                  active ? "text-slate-200" : "text-slate-400"
                }`}
              >
                {metric.description}
              </span>
            </button>
          );
        })}
      </div>

      {showTransportFilters ? (
        <div className="space-y-1.5 px-3 pb-3">
          <p className="px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
            {t("sidebar.stopsToShow")}
          </p>
          {transportTypes.map((transport) => {
            const active = visibleTransportTypes[transport.type];
            return (
              <button
                className={`flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-left transition ${
                  active ? "bg-white text-slate-900 ring-1 ring-slate-900/10" : "bg-white/40 text-slate-400"
                }`}
                key={transport.type}
                onClick={() => onTransportTypeToggle(transport.type)}
                type="button"
              >
                <span
                  className="grid h-7 w-7 shrink-0 place-items-center rounded-full text-[9px] font-bold text-white"
                  style={{ backgroundColor: transport.color }}
                >
                  {transport.icon}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-[13px] font-semibold">{transport.label}</span>
                  <span className="block text-[11px] text-slate-400">
                    {formatNumber(transportTypeCounts[transport.type] ?? 0)} points
                  </span>
                </span>
                <span
                  className={`h-2 w-2 shrink-0 rounded-full ${
                    active ? "bg-emerald-500" : "bg-slate-300"
                  }`}
                />
              </button>
            );
          })}
        </div>
      ) : null}

      <div className="space-y-2 border-t border-slate-900/8 px-3 py-3">
        <p className="px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          {t("sidebar.searchFilters")}
        </p>
        <input
          className="w-full rounded-xl border border-slate-900/8 bg-white/80 px-2.5 py-1.5 text-[13px] text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400"
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder={t("sidebar.searchPlaceholder")}
          type="search"
          value={query}
        />
        <select
          className="w-full rounded-xl border border-slate-900/8 bg-white/80 px-2.5 py-1.5 text-[13px] text-slate-900 outline-none transition focus:border-slate-400"
          onChange={(event) => onArrondissementFilterChange(event.target.value)}
          value={arrondissementFilter}
        >
          <option value="">{t("sidebar.allArr")}</option>
          {arrondissementOptions.map((arrondissement) => (
            <option key={arrondissement} value={arrondissement}>
              {arrondissement}
            </option>
          ))}
        </select>
        <label className="block rounded-xl bg-white/60 p-2.5 text-[11px] font-medium text-slate-500">
          {t("sidebar.minScore")} {minScore.toFixed(1)}/10
          <input
            className="mt-1.5 w-full accent-slate-900"
            max={10}
            min={0}
            onChange={(event) => onMinScoreChange(Number(event.target.value))}
            step={0.5}
            type="range"
            value={minScore}
          />
        </label>
      </div>

      <div className="space-y-1.5 px-3 pb-3">
        <p className="px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          {t("sidebar.topMatches")}
        </p>
        {loadingStates[mainIndicator] ? (
          <div className="space-y-1.5">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 rounded-xl bg-slate-100 animate-pulse" />
            ))}
          </div>
        ) : ranking.length > 0 ? (
          ranking.map((feature) => {
            const isActive = feature.properties.map_id === selectedMapId;
            return (
              <button
                aria-current={isActive ? "true" : undefined}
                className={`flex w-full items-center justify-between gap-2 rounded-xl px-2.5 py-1.5 text-left transition ${
                  isActive
                    ? "bg-emerald-50 ring-2 ring-emerald-500/70 shadow-sm"
                    : "bg-white/60 hover:bg-white"
                }`}
                key={feature.properties.map_id}
                onClick={() => onRankingSelect(feature.properties.map_id)}
                type="button"
              >
                <span className="min-w-0">
                  <span className="block truncate text-[13px] font-semibold text-slate-900">
                    #{feature.properties.active_rank} {feature.properties.name}
                  </span>
                  <span className="block truncate text-[11px] text-slate-400">
                    {feature.properties.arrondissement}
                  </span>
                </span>
                <span
                  className={`shrink-0 text-[13px] font-semibold ${
                    isActive ? "text-emerald-800" : "text-emerald-700"
                  }`}
                >
                  {formatScore(feature.properties.active_score)}
                </span>
              </button>
            );
          })
        ) : (
          <p className="rounded-xl bg-white/60 px-2.5 py-2 text-[13px] text-slate-500">{t("sidebar.noMatch")}</p>
        )}
      </div>

      <div className="mt-auto grid grid-cols-3 gap-1.5 border-t border-slate-900/8 p-3 md:block md:space-y-1.5">
        <Metric label="Zones" value={formatNumber(featureCount)} />
        <Metric label={t("metric.avg")} value={formatScore(averageScore)} />
        <Metric label={t("pillar.school.label")} value={`${schoolShare}%`} />
      </div>
    </div>
  );
}

function Sidebar({
  featureCount,
  averageScore,
  schoolShare,
  loadingStates,
  mainIndicator,
  selectedSubMetric,
  transportTypeCounts,
  visibleTransportTypes,
  arrondissementOptions,
  arrondissementFilter,
  minScore,
  query,
  ranking,
  selectedMapId,
  expanded,
  onToggleExpanded,
  uiHidden,
  mobileSheetOpen,
  onMobileSheetOpenChange,
  onMainIndicatorChange,
  onSubMetricChange,
  onArrondissementFilterChange,
  onMinScoreChange,
  onQueryChange,
  onRankingSelect,
  onTransportTypeToggle,
}: {
  featureCount: number;
  averageScore: number | null;
  schoolShare: number;
  loadingStates: Record<MainIndicator, boolean>;
  mainIndicator: MainIndicator;
  selectedSubMetric: MetricKey;
  transportTypeCounts: Record<TransportType, number>;
  visibleTransportTypes: Record<TransportType, boolean>;
  arrondissementOptions: string[];
  arrondissementFilter: string;
  minScore: number;
  query: string;
  ranking: ComputedFeature[];
  selectedMapId: string | null;
  expanded: boolean;
  onToggleExpanded: () => void;
  uiHidden: boolean;
  mobileSheetOpen: boolean;
  onMobileSheetOpenChange: (open: boolean) => void;
  onMainIndicatorChange: (indicator: MainIndicator) => void;
  onSubMetricChange: (metric: MetricKey) => void;
  onArrondissementFilterChange: (arrondissement: string) => void;
  onMinScoreChange: (score: number) => void;
  onQueryChange: (query: string) => void;
  onRankingSelect: (id: string) => void;
  onTransportTypeToggle: (type: TransportType) => void;
}) {
  const { t } = useI18n();
  const mainIndicatorOptions = useMainIndicatorOptions();
  const showExpandedPanel = expanded && !uiHidden;

  function handleRailClick(key: MainIndicator) {
    onMainIndicatorChange(key);
    if (!uiHidden && !expanded) {
      onToggleExpanded();
    }
    if (!uiHidden) {
      onMobileSheetOpenChange(true);
    } else {
      onMobileSheetOpenChange(false);
    }
  }

  const expandedProps = {
    arrondissementFilter,
    arrondissementOptions,
    averageScore,
    featureCount,
    loadingStates,
    mainIndicator,
    minScore,
    onArrondissementFilterChange,
    onMinScoreChange,
    onQueryChange,
    onRankingSelect: (id: string) => {
      onRankingSelect(id);
      onMobileSheetOpenChange(false);
    },
    onSubMetricChange,
    onTransportTypeToggle,
    query,
    ranking,
    selectedMapId,
    schoolShare,
    selectedSubMetric,
    transportTypeCounts,
    visibleTransportTypes,
  };

  const rail = (
    <nav
      aria-label={t("sidebar.mainIndicators")}
      className="flex shrink-0 flex-row items-center gap-1 overflow-x-auto border-b border-slate-900/8 bg-white/88 px-2 py-2 shadow-[0_10px_40px_rgba(15,23,42,0.06)] backdrop-blur-xl md:h-screen md:w-16 md:flex-col md:gap-1.5 md:border-b-0 md:border-r md:px-1.5 md:py-3"
    >
      <button
        aria-expanded={expanded}
        className="hidden h-9 w-9 shrink-0 items-center justify-center rounded-xl text-slate-600 transition hover:bg-slate-100 md:flex"
        onClick={onToggleExpanded}
        title={expanded ? t("a11y.collapsePanel") : t("a11y.expandPanel")}
        type="button"
      >
        <span className="text-sm font-semibold">{expanded ? "‹" : "›"}</span>
      </button>
      {mainIndicatorOptions.map((indicator) => {
        const active = mainIndicator === indicator.key;
        const isLoading = loadingStates[indicator.key];
        return (
          <button
            className={`group relative flex shrink-0 flex-col items-center justify-center gap-0.5 rounded-xl px-2 py-2 transition md:aspect-square md:w-11 md:px-0 ${
              active
                ? "bg-slate-900 text-white shadow-[0_2px_10px_rgba(15,23,42,0.18)]"
                : "bg-white/70 text-slate-600 hover:bg-white md:bg-transparent"
            }`}
            key={indicator.key}
            onClick={() => handleRailClick(indicator.key)}
            title={`${indicator.label}: ${indicator.description}`}
            type="button"
          >
            {isLoading && (
              <span className="absolute top-0.5 right-0.5 h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse" />
            )}
            <span
              className={`text-[10px] font-bold tracking-tight ${active ? "text-white" : "text-slate-900"}`}
            >
              {indicator.abbr}
            </span>
            <span className={active ? "[&_svg]:text-white" : "[&_svg]:text-slate-500"}>
              <MainIndicatorGlyph indicator={indicator.key} />
            </span>
            <span className="pointer-events-none absolute left-full top-1/2 z-50 ml-2 hidden -translate-y-1/2 whitespace-nowrap rounded-xl bg-slate-900/95 px-2.5 py-1 text-[11px] font-medium text-white opacity-0 shadow-lg ring-1 ring-white/10 backdrop-blur transition-opacity group-hover:opacity-100 md:group-hover:block">
              <span className="font-semibold">{indicator.label}</span>
              <span className="mt-0.5 block max-w-[220px] whitespace-normal text-[10px] font-normal text-slate-300">
                {indicator.description}
              </span>
            </span>
          </button>
        );
      })}
    </nav>
  );

  return (
    <>
      <aside className="pointer-events-auto z-20 flex w-full shrink-0 flex-col md:h-screen md:w-auto md:flex-row">
        {rail}
        {showExpandedPanel ? (
          <div className="hidden h-screen w-[272px] shrink-0 md:flex md:flex-col">
            <SidebarExpandedContent {...expandedProps} />
          </div>
        ) : null}
      </aside>

      {mobileSheetOpen && showExpandedPanel ? (
        <div className="fixed inset-0 z-30 md:hidden">
          <button
            aria-label={t("a11y.closePanel")}
            className="absolute inset-0 bg-slate-950/25"
            onClick={() => onMobileSheetOpenChange(false)}
            type="button"
          />
          <div className="absolute inset-x-0 bottom-0 flex max-h-[min(85vh,640px)] flex-col rounded-t-3xl border border-slate-900/8 bg-white/95 shadow-[0_-12px_48px_rgba(15,23,42,0.12)] backdrop-blur-xl">
            <div className="flex shrink-0 justify-center py-2">
              <span className="h-1 w-10 rounded-full bg-slate-300" />
            </div>
            <div className="flex items-center justify-between border-b border-slate-900/8 px-4 py-2">
              <p className="text-[13px] font-semibold text-slate-900">{t("mobile.indicatorsFilters")}</p>
              <button
                className="rounded-full px-3 py-1 text-[12px] font-medium text-slate-600 hover:bg-slate-100"
                onClick={() => onMobileSheetOpenChange(false)}
                type="button"
              >
                {t("common.close")}
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-hidden">
              <SidebarExpandedContent {...expandedProps} />
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}

function Legend({
  label = "Score",
  onClose,
  showHoverPreview,
  onShowHoverPreviewChange,
}: {
  label?: string;
  onClose: () => void;
  showHoverPreview: boolean;
  onShowHoverPreviewChange: (value: boolean) => void;
}) {
  const { t } = useI18n();
  const stops = [
    { label: "0", color: "#f43f5e" },
    { label: "2", color: "#fb923c" },
    { label: "4", color: "#fbbf24" },
    { label: "6", color: "#a3e635" },
    { label: "8", color: "#22c55e" },
    { label: "10", color: "#047857" },
  ];

  return (
    <GlassCard className="rounded-xl p-2.5">
      <div className="mb-1.5 flex items-start justify-between gap-1.5">
        <div className="min-w-0">
          <p className="text-[12px] font-semibold leading-tight text-slate-950">{label}</p>
          <p className="text-[9px] font-medium text-slate-500">{t("legend.lowToHigh")}</p>
        </div>
        <button
          aria-label={t("a11y.closeLegend")}
          className="shrink-0 rounded-full px-1.5 py-0.5 text-[13px] font-medium leading-none text-slate-500 hover:bg-slate-100"
          onClick={onClose}
          type="button"
        >
          ×
        </button>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-linear-to-r from-rose-500 via-amber-300 to-emerald-700" />
      <div className="mt-1.5 flex flex-wrap justify-between gap-x-0.5 gap-y-0.5 text-[9px] font-medium tabular-nums text-slate-500">
        {stops.map((stop) => (
          <span key={stop.label} className="flex items-center gap-1">
            <span
              className="h-1.5 w-1.5 shrink-0 rounded-full"
              style={{ backgroundColor: stop.color }}
            />
            {stop.label}
          </span>
        ))}
      </div>
      <label className="mt-2 flex cursor-pointer items-center justify-between gap-2 rounded-lg bg-slate-50/90 px-2 py-1.5 text-[10px] font-medium text-slate-600">
        <span>{t("legend.hoverPreview")}</span>
        <input
          checked={showHoverPreview}
          className="h-3.5 w-3.5 accent-slate-900"
          onChange={(e) => onShowHoverPreviewChange(e.target.checked)}
          type="checkbox"
        />
      </label>
    </GlassCard>
  );
}

function WeightPanel({
  weights,
  topFeatures,
  selectedMapId,
  onChange,
  onPreset,
  onRankingSelect,
}: {
  weights: Weights;
  topFeatures: ComputedFeature[];
  selectedMapId: string | null;
  onChange: (key: WeightKey, value: number) => void;
  onPreset: (weights: Weights) => void;
  onRankingSelect: (id: string) => void;
}) {
  const { t, lang } = useI18n();
  const pillarMeta = usePillarMeta();
  const total = Object.values(weights).reduce((sum, weight) => sum + weight, 0);

  return (
    <GlassCard className="max-h-[min(58vh,620px)] overflow-y-auto rounded-2xl p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-[#007AFF]">
            {t("weight.studio")}
          </p>
          <h2 className="mt-1 text-base font-semibold tracking-tight text-slate-950">
            {t("weight.choosePriorities")}
          </h2>
          <p className="mt-1 text-[12px] leading-snug text-slate-500">
            {t("weight.studioDesc")}
          </p>
        </div>
      </div>

      <div className="mt-2 flex flex-wrap gap-1.5">
        <button
          className="rounded-full bg-slate-950 px-2.5 py-1 text-[10px] font-semibold text-white shadow-[0_2px_10px_rgba(15,23,42,0.18)] transition hover:bg-slate-800"
          onClick={() => onPreset(defaultWeights)}
          type="button"
        >
          {t("weight.officialFamily")}
        </button>
        <button
          className="rounded-full border border-slate-900/8 bg-white/70 px-2.5 py-1 text-[10px] font-semibold text-slate-700 transition hover:bg-white"
          onClick={() => onPreset(equalWeights)}
          type="button"
        >
          {t("weight.equalWeights")}
        </button>
      </div>

      <div className="mt-3 space-y-2">
        {pillarMeta.map((pillar) => {
          const share = total > 0 ? Math.round((weights[pillar.key] / total) * 100) : 0;

          return (
            <div key={pillar.key}>
              <div className="mb-1 flex items-center justify-between gap-2">
                <div>
                  <p className="text-[12px] font-semibold text-slate-900">{pillar.label}</p>
                  <p className="text-[10px] leading-snug text-slate-500">{pillar.description}</p>
                </div>
                <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700">
                  {share}%
                </span>
              </div>
              <input
                aria-label={lang === "fr" ? `${t("weight.weightOf")} ${pillar.label}` : `${pillar.label} weight`}
                className="accent-slate-950"
                max={100}
                min={0}
                onChange={(event) =>
                  onChange(pillar.key, clampWeight(Number(event.target.value)))
                }
                step={0.5}
                type="range"
                value={weights[pillar.key]}
              />
            </div>
          );
        })}
      </div>

      <div className="mt-3 rounded-xl bg-slate-950 p-2.5 text-white">
        <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-slate-400">
          {t("weight.currentTop3")}
        </p>
        <div className="mt-1.5 space-y-1.5">
          {topFeatures.slice(0, 3).map((feature) => {
            const isActive = feature.properties.map_id === selectedMapId;
            return (
              <button
                aria-current={isActive ? "true" : undefined}
                className={`flex w-full items-center justify-between gap-2 rounded-lg px-2 py-1 text-left transition ${
                  isActive
                    ? "bg-white/15 ring-1 ring-emerald-400"
                    : "hover:bg-white/10"
                }`}
                key={feature.properties.map_id}
                onClick={() => onRankingSelect(feature.properties.map_id)}
                type="button"
              >
                <span className="min-w-0">
                  <span className="block truncate text-[11px] font-semibold leading-snug">
                    #{feature.properties.active_rank} {feature.properties.name}
                  </span>
                  <span className="block truncate text-[10px] text-slate-400">
                    {feature.properties.arrondissement}
                  </span>
                </span>
                <span className="shrink-0 text-[11px] font-semibold tabular-nums">
                  {formatScore(feature.properties.active_score)}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </GlassCard>
  );
}

function ScoreBreakdown({
  feature,
  weights,
  showWeightContributions,
}: {
  feature: ComputedProperties;
  weights: Weights;
  showWeightContributions: boolean;
}) {
  const { t } = useI18n();
  const pillarMeta = usePillarMeta();
  return (
    <div className="space-y-2">
      {pillarMeta.map((pillar) => {
        const score = feature[pillar.key];
        const share = effectiveWeight(weights, pillar.key);
        const contribution =
          typeof score === "number" ? Number((score * share).toFixed(2)) : null;

        return (
          <div key={pillar.key} className="rounded-lg bg-slate-100/80 p-2">
            <div className="mb-1 flex items-center justify-between gap-1.5">
              <div>
                <p className="text-[12px] font-semibold text-slate-900">{pillar.shortLabel}</p>
                <p className="text-[10px] leading-snug text-slate-500">
                  {showWeightContributions ? (
                    <>
                      {t("score.weight")} {Math.round(share * 100)}% · {t("score.contribution")}{" "}
                      {formatScore(contribution)}
                    </>
                  ) : (
                    <>{t("score.pillarScore")}</>
                  )}
                </p>
              </div>
              <p className="text-[12px] font-semibold tabular-nums text-slate-950">
                {formatScore(score)}
              </p>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-white">
              <div
                className="h-full rounded-full"
                style={{
                  backgroundColor: pillar.color,
                  width: `${Math.max(0, Math.min((score ?? 0) * 10, 100))}%`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function DetailsPanel({
  selected,
  topFeature,
  averageScore,
  featureCount,
  weights,
  mainIndicator,
  selectedMetric,
  bdcomData,
  dvfData,
  irisDataLoading,
  priceLookup,
  onClose,
  onDismissPanel,
}: {
  selected: ComputedProperties | null;
  topFeature: ComputedFeature | null;
  averageScore: number | null;
  featureCount: number;
  weights: Weights;
  mainIndicator: MainIndicator;
  selectedMetric: MetricKey;
  priceLookup: Record<string, { prix_m2?: number; loyer_median_m2?: number }>;
  bdcomData: BdcomIrisStats | null;
  dvfData: DvfIrisStats | null;
  irisDataLoading: boolean;
  onClose: () => void;
  onDismissPanel: () => void;
}) {
  const { t } = useI18n();
  const metricMeta = useMetricMeta();
  const pillarMeta = usePillarMeta();
  const feature = selected ?? topFeature?.properties ?? null;
  const metricLabel = metricMeta[selectedMetric]?.label ?? "Score";
  const isVivabilite = mainIndicator === "vivabilite";
  const priceInfo = feature?.arrondissement ? priceLookup[feature.arrondissement] : undefined;
  const displayPrixM2 = feature?.prix_m2 ?? priceInfo?.prix_m2;
  const displayLoyerM2 = feature?.loyer_median_m2 ?? priceInfo?.loyer_median_m2;
  const bestPillar = feature && isVivabilite
    ? pillarMeta
        .map((pillar) => ({ ...pillar, value: feature[pillar.key] }))
        .filter((pillar) => typeof pillar.value === "number")
        .sort((a, b) => (b.value ?? 0) - (a.value ?? 0))[0]
    : null;
  const weakestPillar = feature && isVivabilite
    ? pillarMeta
        .map((pillar) => ({ ...pillar, value: feature[pillar.key] }))
        .filter((pillar) => typeof pillar.value === "number")
        .sort((a, b) => (a.value ?? 0) - (b.value ?? 0))[0]
    : null;

  const headlineHint =
    selectedMetric === "family_mix"
      ? t("details.familyMixHint")
      : `${metricMeta[selectedMetric]?.description ?? ""} ${t("details.coloredHint")}`;

  return (
    <GlassCard className="max-h-[min(62vh,640px)] w-full overflow-y-auto rounded-t-2xl p-3 md:w-[min(100%,320px)] md:rounded-2xl">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-emerald-700">
            {selected ? t("details.selectedArea") : t("details.bestMatch")}
          </p>
          <h2 className="mt-1 truncate text-[15px] font-semibold leading-snug tracking-tight text-slate-950">
            {feature?.name ?? metricLabel}
          </h2>
          <p className="mt-0.5 text-[11px] leading-snug text-slate-500">
            {feature?.arrondissement ?? `${featureCount} ${t("details.mappedZonesSuffix")}`}
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1">
          <button
            className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 transition hover:bg-slate-200"
            onClick={selected ? onClose : onDismissPanel}
            type="button"
          >
            {t("common.close")}
          </button>
        </div>
      </div>

      <div className="mt-2.5 grid grid-cols-2 gap-1.5">
        <Metric
          label={metricLabel}
          tone="green"
          value={formatScore(feature?.active_score ?? averageScore)}
        />
        <Metric
          label={t("details.dynamicRank")}
          tone="dark"
          value={feature?.active_rank ? `#${feature.active_rank}` : t("common.na")}
        />
      </div>

      <div className="mt-1.5 grid grid-cols-3 gap-1.5">
        <Metric
          label={isVivabilite ? t("details.original") : t("metric.avg")}
          value={formatScore(isVivabilite ? feature?.vivabilite_score : averageScore)}
        />
        {mainIndicator !== "thermal" ? (
          <Metric
            label={t("details.delta")}
            value={
              typeof feature?.score_delta === "number"
                ? `${feature.score_delta >= 0 ? "+" : ""}${feature.score_delta.toFixed(1)}`
                : t("common.na")
            }
          />
            ) : null}
            <Metric
              label={t("details.percentile")}
              value={
                typeof feature?.active_percentile === "number"
                  ? `${feature.active_percentile}%`
                  : t("common.na")
              }
            />
          </div>

      {feature?.no_data ? (
        /* ── No-data zone: show reason instead of blank metrics ── */
        <>
          <div className="mt-2.5 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-[10px] font-semibold text-slate-700">
              {feature.typ_iris === "A"
                ? t("zone.activityNotScored")
                : feature.typ_iris === "D"
                ? t("zone.specialNotScored")
                : t("zone.residentialGap")}
            </p>
            <p className="mt-1 text-[10px] leading-relaxed text-slate-500">
              {feature.typ_iris === "A"
                ? t("zone.activityDesc")
                : feature.typ_iris === "D"
                ? t("zone.specialDesc")
                : t("zone.residentialDesc")}
            </p>
          </div>

          {/* Still show IRIS code so it can be identified */}
          <div className="mt-2 rounded-xl border border-slate-900/8 bg-white/55 p-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-500">{t("details.irisCode")}</span>
              <span className="font-mono text-[10px] font-semibold text-slate-950">
                {feature.code_iris ?? t("common.na")}
              </span>
            </div>
            <div className="mt-1.5 flex items-center justify-between text-[11px]">
              <span className="text-slate-500">{t("details.zoneType")}</span>
              <span className="font-semibold text-slate-950">
                {feature.typ_iris === "A"
                  ? t("zone.typeA")
                  : feature.typ_iris === "D"
                  ? t("zone.typeD")
                  : t("zone.typeH")}
              </span>
            </div>
          </div>
        </>
      ) : (
        /* ── Scored zone: full metrics ── */
        <>
          <div className="mt-2.5">
            <Metric
              hint={headlineHint}
              label={metricLabel}
              tone="green"
              value={formatScore(feature?.active_score ?? averageScore)}
            />
          </div>

          <div className="mt-2 rounded-xl border border-slate-900/8 bg-white/55 p-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-500">
                {feature?.geography === "arrondissement" ? t("details.level") : "Population"}
              </span>
              <span className="font-semibold text-slate-950">
                {feature?.geography === "arrondissement"
                  ? "Arrondissement"
                  : formatNumber(feature?.population)}
              </span>
            </div>
            <div className="mt-1.5 flex items-center justify-between text-[11px]">
              <span className="text-slate-500">
                {feature?.geography === "arrondissement" ? t("details.arrCode") : t("details.irisCode")}
              </span>
              <span className="font-mono text-[10px] font-semibold text-slate-950">
                {feature?.code_iris ?? feature?.code_arrondissement ?? t("common.na")}
              </span>
            </div>
            {typeof displayLoyerM2 === "number" ? (
              <div className="mt-1.5 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">{t("details.medianRent")}</span>
                <span className="font-semibold text-slate-950">
                  {displayLoyerM2.toFixed(1)} €/m²
                </span>
              </div>
            ) : null}
            {typeof displayPrixM2 === "number" ? (
              <div className="mt-1.5 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">{t("details.medianSale")}</span>
                <span className="font-semibold text-slate-950">
                  {formatNumber(displayPrixM2)} €/m²
                </span>
              </div>
            ) : null}
            {typeof feature?.densite_arbres === "number" ? (
              <div className="mt-1.5 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">{t("sub.treedensity.label")}</span>
                <span className="font-semibold text-slate-950">
                  {feature.densite_arbres.toFixed(1)} trees/ha
                </span>
              </div>
            ) : null}
          </div>

          {feature && isVivabilite ? (
            <div className="mt-2.5">
              <ScoreBreakdown
                feature={feature}
                showWeightContributions={selectedMetric === "family_mix"}
                weights={weights}
              />
            </div>
          ) : null}
        </>
      )}

      {bestPillar && weakestPillar ? (
        <div className="mt-2 grid grid-cols-2 gap-1.5">
          <div className="rounded-lg bg-emerald-50 p-2">
            <p className="text-[9px] font-medium text-emerald-700">{t("details.strongestPillar")}</p>
            <p className="mt-0.5 text-[11px] font-semibold leading-snug text-slate-950">
              {bestPillar.shortLabel} · {formatScore(bestPillar.value)}
            </p>
          </div>
          <div className="rounded-lg bg-rose-50 p-2">
            <p className="text-[9px] font-medium text-rose-700">{t("details.weakestPillar")}</p>
            <p className="mt-0.5 text-[11px] font-semibold leading-snug text-slate-950">
              {weakestPillar.shortLabel} · {formatScore(weakestPillar.value)}
            </p>
          </div>
        </div>
      ) : null}

      {mainIndicator === "thermal" ? (
        <>
          {typeof (feature as any)?.cooling_area_score === "number" ? (
            <div className="mt-1.5 flex items-center justify-between text-[11px]">
              <span className="text-slate-500">{t("details.coolingAreaScore")}</span>
              <span className="font-semibold text-slate-950">
                {formatScore((feature as any).cooling_area_score)}
              </span>
            </div>
          ) : null}
          {typeof (feature as any)?.proximity_score === "number" ? (
            <div className="mt-1.5 flex items-center justify-between text-[11px]">
              <span className="text-slate-500">{t("sub.proximity.label")}</span>
              <span className="font-semibold text-slate-950">
                {formatScore((feature as any).proximity_score)}
              </span>
            </div>
          ) : null}
        </>
      ) : null}

      {mainIndicator === "demographics" && typeof (feature as any)?.revenu_median === "number" ? (
        <div className="mt-1.5 flex items-center justify-between text-[11px]">
          <span className="text-slate-500">{t("demo.medianIncome")}</span>
          <span className="font-semibold text-slate-950">
            {formatNumber((feature as any).revenu_median)} €/an
          </span>
        </div>
      ) : null}
      {mainIndicator === "demographics" && typeof (feature as any)?.gini === "number" ? (
        <div className="mt-1.5 flex items-center justify-between text-[11px]">
          <span className="text-slate-500">{t("demo.gini")}</span>
          <span className="font-semibold text-slate-950">
            {((feature as any).gini as number).toFixed(3)}
          </span>
        </div>
      ) : null}
      {mainIndicator === "demographics" && typeof (feature as any)?.pct_cadres === "number" ? (
        <div className="mt-1.5 flex items-center justify-between text-[11px]">
          <span className="text-slate-500">{t("demo.executives")}</span>
          <span className="font-semibold text-slate-950">
            {((feature as any).pct_cadres as number).toFixed(1)}%
          </span>
        </div>
      ) : null}
      {mainIndicator === "demographics" && typeof (feature as any)?.taux_pauvrete === "number" ? (
        <div className="mt-1.5 flex items-center justify-between text-[11px]">
          <span className="text-slate-500">{t("demo.povertyRate")}</span>
          <span className="font-semibold text-slate-950">
            {((feature as any).taux_pauvrete as number).toFixed(1)}%
          </span>
        </div>
      ) : null}

      {selected ? (
        <div className="mt-2.5">
          <p className="px-0.5 text-[9px] font-semibold uppercase tracking-[0.14em] text-slate-400">
            {t("commerce.title")}
          </p>
          {irisDataLoading ? (
            <p className="mt-1 rounded-xl bg-slate-100/80 px-2.5 py-2 text-[11px] text-slate-500">
              {t("common.loadingZone")}
            </p>
          ) : (
            <div className="mt-1 space-y-1.5">
              {bdcomData ? (
                <div className="rounded-xl bg-slate-100/80 p-2">
                  <p className="text-[10px] font-semibold text-slate-700">Commercial</p>
                  <div className="mt-1 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500">{t("commerce.establishments")}</span>
                    <span className="font-semibold text-slate-950">{formatNumber(bdcomData.total_establishments)}</span>
                  </div>
                  {bdcomData.avg_surface_m2 > 0 ? (
                    <div className="mt-1 flex items-center justify-between text-[11px]">
                      <span className="text-slate-500">{t("commerce.avgSurface")}</span>
                      <span className="font-semibold text-slate-950">{bdcomData.avg_surface_m2.toFixed(0)} m²</span>
                    </div>
                  ) : null}
                  {bdcomData.top_activities.length > 0 ? (
                    <div className="mt-1 flex items-start justify-between gap-1 text-[11px]">
                      <span className="shrink-0 text-slate-500">{t("commerce.topActivity")}</span>
                      <span className="text-right font-semibold leading-snug text-slate-950">{bdcomData.top_activities[0]?.activity}</span>
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="rounded-xl bg-slate-100/80 px-2.5 py-2 text-[11px] text-slate-400">
                  {t("commerce.noCommercial")}
                </div>
              )}
              {dvfData ? (
                <div className="rounded-xl bg-slate-100/80 p-2">
                  <p className="text-[10px] font-semibold text-slate-700">Transactions (DVF)</p>
                  <div className="mt-1 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500">Transactions</span>
                    <span className="font-semibold text-slate-950">{formatNumber(dvfData.total_transactions)}</span>
                  </div>
                  {dvfData.median_prix_m2 > 0 ? (
                    <div className="mt-1 flex items-center justify-between text-[11px]">
                      <span className="text-slate-500">{t("commerce.medianM2")}</span>
                      <span className="font-semibold text-slate-950">{formatNumber(Math.round(dvfData.median_prix_m2))} €</span>
                    </div>
                  ) : null}
                  {dvfData.median_surface_m2 > 0 ? (
                    <div className="mt-1 flex items-center justify-between text-[11px]">
                      <span className="text-slate-500">{t("commerce.medianSurface")}</span>
                      <span className="font-semibold text-slate-950">{dvfData.median_surface_m2.toFixed(0)} m²</span>
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="rounded-xl bg-slate-100/80 px-2.5 py-2 text-[11px] text-slate-400">
                  {t("commerce.noTransaction")}
                </div>
              )}
            </div>
          )}
        </div>
      ) : null}
    </GlassCard>
  );
}

function EnhancedMapDashboardInner() {
  const { t, lang, setLang } = useI18n();
  const mainIndicatorOptions = useMainIndicatorOptions();
  const metricMeta = useMetricMeta();
  const subMetricOptions = useSubMetricOptions();
  const [vivabiliteData, setVivabiliteData] =
    useState<VivabiliteFeatureCollection | null>(null);
  const [arrData, setArrData] = useState<VivabiliteFeatureCollection | null>(null);
  const [currentZoom, setCurrentZoom] = useState(initialViewState.zoom ?? ZOOM_BREAK);
  const [thermalData, setThermalData] = useState<IndicatorMapFeatureCollection | null>(
    null,
  );
  const [rentData, setRentData] = useState<IndicatorMapFeatureCollection | null>(null);
  const [saleData, setSaleData] = useState<IndicatorMapFeatureCollection | null>(null);
  const [saleTimeline, setSaleTimeline] =
    useState<SaleTimelineFeatureCollection | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [demographicsData, setDemographicsData] = useState<IndicatorMapFeatureCollection | null>(null);
  const [transportPoints, setTransportPoints] = useState<TransportPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [transportError, setTransportError] = useState<string | null>(null);
  const [loadingStates, setLoadingStates] = useState<Record<MainIndicator, boolean>>({
    vivabilite: true,
    transport: false,
    thermal: false,
    housing: false,
    demographics: false,
  });
  const setLayerLoading = (indicator: MainIndicator, value: boolean) =>
    setLoadingStates((prev) => ({ ...prev, [indicator]: value }));
  const [weights, setWeights] = useState<Weights>(defaultWeights);
  const [mainIndicator, setMainIndicator] = useState<MainIndicator>("vivabilite");
  const [selectedMetric, setSelectedMetric] = useState<MetricKey>("vivabilite_score");
  const [query, setQuery] = useState("");
  const [arrondissementFilter, setArrondissementFilter] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [visibleTransportTypes, setVisibleTransportTypes] = useState<
    Record<TransportType, boolean>
  >({
    bus: true,
    metro: true,
    rail: true,
    tram: true,
    velib: true,
  });
  const [hoveredCode, setHoveredCode] = useState<string | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const mapRef = useRef<MapRef | null>(null);
  const [selectedTransportPoint, setSelectedTransportPoint] =
    useState<TransportPointProperties | null>(null);
  const [popup, setPopup] = useState<{ longitude: number; latitude: number } | null>(
    null,
  );
  const [transportPopup, setTransportPopup] = useState<{
    longitude: number;
    latitude: number;
  } | null>(null);
  const [hoverPopup, setHoverPopup] = useState<{
    longitude: number;
    latitude: number;
  } | null>(null);
  const [showMapIntro, setShowMapIntro] = useState(false);
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  const [uiHidden, setUiHidden] = useState(false);
  const [showTitleCard, setShowTitleCard] = useState(true);
  const [showLegend, setShowLegend] = useState(true);
  const [showDetails, setShowDetails] = useState(true);
  const [showHoverPreview, setShowHoverPreview] = useState(true);
  const [mobileSheetOpen, setMobileSheetOpen] = useState(false);
  const [bdcomIrisData, setBdcomIrisData] = useState<BdcomIrisStats | null>(null);
  const [dvfIrisData, setDvfIrisData] = useState<DvfIrisStats | null>(null);
  const [irisDataLoading, setIrisDataLoading] = useState(false);

  useEffect(() => {
    if (uiHidden) {
      setMobileSheetOpen(false);
    }
  }, [uiHidden]);

  useEffect(() => {
    let active = true;

    fetchVivabiliteMap()
      .then((geojson) => {
        if (!active) {
          return;
        }
        setVivabiliteData(geojson);
        setError(null);
      })
      .catch((err: Error) => {
        if (!active) {
          return;
        }
        setError(err.message);
      })
      .finally(() => {
        if (active) setLayerLoading("vivabilite", false);
      });

    fetchVivabiliteArrondissement()
      .then((geojson) => {
        if (!active) return;
        setArrData(geojson);
      })
      .catch(() => {
        /* arrondissement layer is optional — silently ignore */
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadLayer() {
      if (
        (mainIndicator === "vivabilite" && vivabiliteData) ||
        (mainIndicator === "transport" && vivabiliteData) ||
        (mainIndicator === "thermal" && thermalData) ||
        (mainIndicator === "housing" && selectedMetric === "rent_score" && rentData) ||
        (mainIndicator === "housing" && selectedMetric === "sale_score" && saleData) ||
        (mainIndicator === "demographics" && demographicsData)
      ) {
        setLayerLoading(mainIndicator, false);
        setError(null);
        return;
      }

      setLayerLoading(mainIndicator, true);
      setError(null);

      try {
        if (mainIndicator === "thermal") {
          const geojson = await fetchThermalComfortMap();
          if (active) {
            setThermalData(geojson);
          }
        } else if (mainIndicator === "housing" && selectedMetric === "rent_score") {
          const geojson = await fetchRentMap();
          if (active) {
            setRentData(geojson);
          }
        } else if (mainIndicator === "housing" && selectedMetric === "sale_score") {
          const geojson = await fetchSaleMap();
          if (active) {
            setSaleData(geojson);
          }
        } else if (mainIndicator === "demographics") {
          const geojson = await fetchDemographicsMap();
          if (active) {
            setDemographicsData(geojson);
        }
        } else {
          const geojson = await fetchVivabiliteMap();
          if (active) {
            setVivabiliteData(geojson);
          }
        }

      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Map layer unavailable");
        }
      } finally {
        if (active) {
          setLayerLoading(mainIndicator, false);
        }
      }
    }

    loadLayer();

    return () => {
      active = false;
    };
  }, [mainIndicator, rentData, saleData, selectedMetric, thermalData, vivabiliteData]);

  // Load the quarterly sale-price series the first time the sale layer is shown.
  useEffect(() => {
    if (mainIndicator !== "housing" || selectedMetric !== "sale_score") return;
    if (saleTimeline) return;

    let active = true;
    fetchSaleTimeline()
      .then((timeline) => {
        if (!active) return;
        setSaleTimeline(timeline);
        setSelectedPeriod(
          (prev) => prev ?? timeline.periods[timeline.periods.length - 1] ?? null,
        );
      })
      .catch(() => {
        /* timeline is optional — the static sale layer still renders */
      });

    return () => {
      active = false;
    };
  }, [mainIndicator, selectedMetric, saleTimeline]);

  // Timeline playback: advance through quarters, stopping at the most recent.
  useEffect(() => {
    if (!isPlaying || !saleTimeline) return;

    const periods = saleTimeline.periods;
    const interval = window.setInterval(() => {
      setSelectedPeriod((current) => {
        const index = current ? periods.indexOf(current) : -1;
        const next = index + 1;
        if (next >= periods.length) {
          setIsPlaying(false);
          return periods[periods.length - 1] ?? current;
        }
        return periods[next];
      });
    }, 600);

    return () => window.clearInterval(interval);
  }, [isPlaying, saleTimeline]);

  // Transport points (~5k features) are only rendered on the transport layer,
  // so defer the fetch until that layer is selected and load it just once.
  useEffect(() => {
    if (mainIndicator !== "transport") return;
    if (transportPoints.length > 0) return;

    let active = true;

    fetchTransportPoints()
      .then((points) => {
        if (!active) {
          return;
        }
        setTransportPoints(points);
        setTransportError(null);
      })
      .catch((err: Error) => {
        if (!active) {
          return;
        }
        setTransportError(err.message);
      });

    return () => {
      active = false;
    };
  }, [mainIndicator, transportPoints.length]);

  useEffect(() => {
    if (!selectedCode || !/^\d{9}$/.test(selectedCode)) {
      setBdcomIrisData(null);
      setDvfIrisData(null);
      setIrisDataLoading(false);
      return;
    }

    let active = true;
    // The detail panel's price card needs the arrondissement rent/sale layers.
    // Fetch each once and reuse — don't refetch on every zone click.
    if (!rentData || !saleData) {
      Promise.all([
        rentData ?? fetchRentMap(),
        saleData ?? fetchSaleMap(),
      ])
        .then(([rent, sale]) => {
          if (!active) return;
          setRentData((prev) => prev ?? rent);
          setSaleData((prev) => prev ?? sale);
        })
        .catch(() => {});
    }
    setIrisDataLoading(true);

    Promise.all([
      fetchBdcomByIris(selectedCode).catch(() => null),
      fetchDvfByIris(selectedCode).catch(() => null),
    ]).then(([bdcom, dvf]) => {
      if (!active) return;
      setBdcomIrisData(bdcom);
      setDvfIrisData(dvf);
      setIrisDataLoading(false);
    });

    return () => {
      active = false;
    };
  }, [selectedCode]);

  // Sale layer recolored for the period picked on the timeline. Each feature's
  // sale_score / prix_m2 are swapped for the selected quarter's values.
  const saleTimelineSnapshot = useMemo<IndicatorMapFeatureCollection | null>(() => {
    if (!saleTimeline || !selectedPeriod) return null;
    return {
      type: "FeatureCollection",
      features: saleTimeline.features.map((feature) => ({
        ...feature,
        properties: {
          ...feature.properties,
          sale_score: feature.properties.scores_by_period?.[selectedPeriod] ?? null,
          prix_m2: feature.properties.prices_by_period?.[selectedPeriod] ?? null,
          date_periode: selectedPeriod,
        },
      })),
    };
  }, [saleTimeline, selectedPeriod]);

  const sourceData = useMemo(() => {
    if (mainIndicator === "thermal") return thermalData;
    if (mainIndicator === "housing")
      return selectedMetric === "sale_score"
        ? saleTimelineSnapshot ?? saleData
        : rentData;
    if (mainIndicator === "demographics") return demographicsData;
    // vivabilite & transport: use arrondissement layer when zoomed out
    if (currentZoom < ZOOM_BREAK && arrData) return arrData;
    return vivabiliteData;
  }, [mainIndicator, rentData, saleData, saleTimelineSnapshot, selectedMetric, thermalData, vivabiliteData, currentZoom, arrData, demographicsData]);

  const computedData = useMemo(
    () => buildComputedGeojson(sourceData, weights, selectedMetric),
    [sourceData, selectedMetric, weights],
  );
  const displayData = useMemo(
    () => filterComputedGeojson(computedData, query, arrondissementFilter, minScore),
    [arrondissementFilter, computedData, minScore, query],
  );
  const transportData = useMemo(
    () => buildTransportGeojson(transportPoints, visibleTransportTypes),
    [transportPoints, visibleTransportTypes],
  );

  const stats = useMemo(() => {
    const features = displayData?.features ?? [];
    const scores = features
      .map((feature) => feature.properties.active_score)
      .filter((score): score is number => typeof score === "number");
    const averageScore =
      scores.length > 0
        ? scores.reduce((sum, score) => sum + score, 0) / scores.length
        : null;
    const topFeatures = [...features]
      .filter((feature) => typeof feature.properties.active_rank === "number")
      .sort(
        (a, b) =>
          (a.properties.active_rank ?? Infinity) -
          (b.properties.active_rank ?? Infinity),
      );

    return {
      averageScore,
      topFeature: topFeatures[0] ?? null,
      topFeatures: topFeatures.slice(0, 5),
      featureCount: features.length,
    };
  }, [displayData]);

  const priceLookup = useMemo(() => {
    const lookup: Record<string, { prix_m2?: number; loyer_median_m2?: number }> = {};
    saleData?.features.forEach((f) => {
      const arr = f.properties.arrondissement;
      if (arr && typeof f.properties.prix_m2 === "number") {
        lookup[arr] = { ...lookup[arr], prix_m2: f.properties.prix_m2 };
      }
    });
    rentData?.features.forEach((f) => {
      const arr = f.properties.arrondissement;
      if (arr && typeof f.properties.loyer_median_m2 === "number") {
        lookup[arr] = { ...lookup[arr], loyer_median_m2: f.properties.loyer_median_m2 };
      }
    });
    return lookup;
  }, [saleData, rentData]);

  const selected =
    displayData?.features.find((feature) => feature.properties.map_id === selectedCode)
      ?.properties ?? null;
  const hovered =
    displayData?.features.find((feature) => feature.properties.map_id === hoveredCode)
      ?.properties ?? null;
  const hoverAllowed = !uiHidden && showHoverPreview;
  const popupFeature = uiHidden
    ? null
    : (selected ?? (hoverAllowed ? hovered : null));
  const popupPosition = uiHidden
    ? null
    : selected
      ? popup
      : hoverAllowed
        ? hoverPopup
        : null;
  const activeCode = selectedCode ?? hoveredCode ?? "";
  const sidebarMapInsetClass =
    !uiHidden && sidebarExpanded ? "md:left-[336px]" : "md:left-16";
  const schoolShare = Math.round(effectiveWeight(weights, "school_score") * 100);
  const showTransportMarkers = mainIndicator === "transport";
  const showWeightStudio = mainIndicator === "vivabilite" && selectedMetric === "family_mix";
  const metricLabel = metricMeta[selectedMetric]?.label ?? "Score";
  const mainLabel =
    mainIndicatorOptions.find((indicator) => indicator.key === mainIndicator)?.label ??
    "Urban indicator";
  const arrondissementOptions = useMemo(() => {
    const arrondissements = new Set<string>();
    computedData?.features.forEach((feature) => {
      if (feature.properties.arrondissement) {
        arrondissements.add(feature.properties.arrondissement);
      }
    });
    return [...arrondissements].sort((a, b) => a.localeCompare(b, "fr"));
  }, [computedData]);
  const transportTypeCounts = useMemo(
    () =>
      transportTypes.reduce(
        (counts, transport) => {
          counts[transport.type] = transportPoints.filter(
            (point) => point.type === transport.type,
          ).length;
          return counts;
        },
        {
          bus: 0,
          metro: 0,
          rail: 0,
          tram: 0,
          velib: 0,
        } as Record<TransportType, number>,
      ),
    [transportPoints],
  );

  const activeLayer: LayerProps = {
    id: "vivabilite-active",
    type: "line",
    filter: ["==", ["get", "map_id"], activeCode],
    paint: {
      "line-color": "#020617",
      "line-width": ["interpolate", ["linear"], ["zoom"], 10, 2, 14, 4],
      "line-opacity": activeCode ? 1 : 0,
    },
  };

  function flyToFeature(mapId: string) {
    const feature = displayData?.features.find(
      (item) => item.properties.map_id === mapId,
    );
    const map = mapRef.current;
    if (!feature?.geometry || !map) return;
    const bounds = geometryBounds(feature.geometry);
    if (!bounds) return;
    map.fitBounds(bounds, { padding: 64, maxZoom: 15, duration: 900 });
  }

  /** Select a zone from a ranking list: highlight it, open details, zoom in. */
  function selectRankedZone(mapId: string) {
    setSelectedCode(mapId);
    setPopup(null);
    setSelectedTransportPoint(null);
    setTransportPopup(null);
    setShowDetails(true);
    flyToFeature(mapId);
  }

  function handleMouseMove(event: InteractiveMapEvent) {
    const feature = event.features?.[0];
    if (feature?.layer?.id?.startsWith("transport")) {
      event.target.getCanvas().style.cursor = "pointer";
      setHoveredCode(null);
      setHoverPopup(null);
      return;
    }

    const properties = getFeatureProperties(event);
    event.target.getCanvas().style.cursor = properties ? "pointer" : "";
    setHoveredCode(properties?.map_id ?? null);
    setHoverPopup(
      properties
        ? { longitude: event.lngLat.lng, latitude: event.lngLat.lat }
        : null,
    );
  }

  function handleMouseLeave(event: InteractiveMapEvent) {
    event.target.getCanvas().style.cursor = "";
    setHoveredCode(null);
    setHoverPopup(null);
  }

  function handleClick(event: InteractiveMapEvent) {
    const feature = event.features?.[0];
    if (
      feature?.layer?.id === "transport-points" ||
      feature?.layer?.id === "transport-point-labels"
    ) {
      const point = getTransportProperties(event);
      if (!point) {
        return;
      }

      setSelectedTransportPoint(point);
      setTransportPopup({ longitude: event.lngLat.lng, latitude: event.lngLat.lat });
      setSelectedCode(null);
      setPopup(null);
      return;
    }
    if (feature?.layer?.id?.startsWith("transport")) {
      return;
    }

    const properties = getFeatureProperties(event);
    if (!properties) {
      return;
    }

    setSelectedCode(properties.map_id);
    setPopup({ longitude: event.lngLat.lng, latitude: event.lngLat.lat });
    setSelectedTransportPoint(null);
    setTransportPopup(null);
    setShowDetails(true);

    const zoneId =
      (typeof properties.code_iris === "string" && properties.code_iris.trim()) ||
      String(properties.map_id ?? "").trim();
    if (zoneId) {
      const geo = properties.geography;
      recordZoneClick({
        user_key: getAnalyticsUserKey(),
        zone_id: zoneId,
        zone_name: typeof properties.name === "string" ? properties.name : null,
        geography:
          geo === "iris" || geo === "arrondissement" ? geo : undefined,
      });
    }
  }

  function changeMainIndicator(indicator: MainIndicator) {
    setMainIndicator(indicator);
    setSelectedMetric(subMetricOptions[indicator][0].key);
    setArrondissementFilter("");
    setMinScore(0);
    setQuery("");
    setSelectedCode(null);
    setPopup(null);
    setSelectedTransportPoint(null);
    setTransportPopup(null);
  }

  function changeMetric(metric: MetricKey) {
    setSelectedMetric(metric);
    setSelectedCode(null);
    setPopup(null);
    setSelectedTransportPoint(null);
    setTransportPopup(null);
  }

  function toggleTransportType(type: TransportType) {
    setVisibleTransportTypes((current) => ({ ...current, [type]: !current[type] }));
  }

  function updateWeight(key: WeightKey, value: number) {
    setWeights((current) => ({ ...current, [key]: value }));
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#f5f5f7] font-[ui-sans-serif,-apple-system,BlinkMacSystemFont,'SF_Pro_Text',Inter,system-ui] text-slate-950 antialiased">
      <div
        aria-hidden
        className="pointer-events-none absolute left-0 top-0 z-0 hidden h-full w-[min(480px,45vw)] bg-[radial-gradient(ellipse_at_0%_20%,rgba(16,185,129,0.06),transparent_55%)] md:block"
      />
      <div className="absolute inset-x-0 top-0 z-20 md:bottom-0 md:left-0 md:right-auto">
        <Sidebar
          averageScore={stats.averageScore}
          arrondissementFilter={arrondissementFilter}
          arrondissementOptions={arrondissementOptions}
          expanded={sidebarExpanded}
          featureCount={stats.featureCount}
          loadingStates={loadingStates}
          mainIndicator={mainIndicator}
          minScore={minScore}
          mobileSheetOpen={mobileSheetOpen}
          onArrondissementFilterChange={setArrondissementFilter}
          onMainIndicatorChange={changeMainIndicator}
          onMinScoreChange={setMinScore}
          onMobileSheetOpenChange={setMobileSheetOpen}
          onQueryChange={setQuery}
          onRankingSelect={selectRankedZone}
          onSubMetricChange={changeMetric}
          onToggleExpanded={() => setSidebarExpanded((v) => !v)}
          onTransportTypeToggle={toggleTransportType}
          query={query}
          ranking={stats.topFeatures}
          selectedMapId={selectedCode}
          selectedSubMetric={selectedMetric}
          schoolShare={schoolShare}
          transportTypeCounts={transportTypeCounts}
          uiHidden={uiHidden}
          visibleTransportTypes={visibleTransportTypes}
        />
      </div>

      <div
        className={`absolute inset-0 z-0 pt-[52px] md:pt-0 ${sidebarMapInsetClass}`}
      >
        <Map
          ref={mapRef}
          initialViewState={initialViewState}
          interactiveLayerIds={[
            "vivabilite-fill",
            "transport-points",
            "transport-clusters",
          ]}
          mapStyle={mapStyle}
          mapboxAccessToken={mapboxToken}
          maxBounds={ileDeFranceMaxBounds}
          maxZoom={20}
          minZoom={6}
          onClick={handleClick}
          onMouseLeave={handleMouseLeave}
          onMouseMove={handleMouseMove}
          onMove={(e) => setCurrentZoom(e.viewState.zoom)}
          reuseMaps
          style={{ height: "100%", width: "100%" }}
        >
          <NavigationControl position="bottom-right" />
          <Source
            data={displayData ?? { type: "FeatureCollection", features: [] }}
            id="vivabilite-source"
            type="geojson"
          >
            <Layer {...fillLayer} />
            <Layer {...outlineLayer} />
            <Layer {...activeLayer} />
          </Source>

          {showTransportMarkers ? (
            <Source
              cluster
              clusterMaxZoom={13}
              clusterRadius={42}
              data={transportData}
              id="transport-source"
              type="geojson"
            >
              <Layer {...transportClusterLayer} />
              <Layer {...transportClusterCountLayer} />
              <Layer {...transportPointCircleLayer} />
              <Layer {...transportPointLabelLayer} />
            </Source>
          ) : null}

          {popupFeature && popupPosition ? (
            <Popup
              anchor="bottom"
              closeButton={Boolean(selected)}
              closeOnClick={false}
              latitude={popupPosition.latitude}
              longitude={popupPosition.longitude}
              offset={12}
              onClose={() => {
                setSelectedCode(null);
                setPopup(null);
              }}
            >
              <div className="max-w-[200px] p-1.5">
                <p className="text-[8px] font-semibold uppercase tracking-wide text-emerald-700">
                  {selected ? t("popup.selected") : t("popup.preview")}
                </p>
                <p className="mt-0.5 line-clamp-2 text-[11px] font-semibold leading-snug text-slate-950">
                  {popupFeature.name}
                </p>
                {popupFeature.no_data ? (
                  <div className="mt-1 rounded-md bg-slate-100 px-2 py-1.5">
                    <p className="text-[9px] font-semibold text-slate-600">
                      {popupFeature.typ_iris === "A"
                        ? t("popup.activityZone")
                        : popupFeature.typ_iris === "D"
                        ? t("popup.specialZone")
                        : t("popup.residentialGap")}
                    </p>
                    <p className="mt-0.5 text-[8px] leading-snug text-slate-400">
                      {popupFeature.typ_iris === "A"
                        ? t("popup.activityDesc")
                        : popupFeature.typ_iris === "D"
                        ? t("popup.specialDesc")
                        : t("popup.residentialDesc")}
                    </p>
                  </div>
                ) : (
                  <div className="mt-1 grid grid-cols-2 gap-1 text-[10px]">
                    <div className="rounded-md bg-blue-50 px-1.5 py-1">
                      <p className="text-[8px] font-medium text-[#007AFF]">Score</p>
                      <p className="font-semibold tabular-nums text-slate-950">
                        {formatScore(popupFeature.active_score)}
                      </p>
                    </div>
                    <div className="rounded-md bg-slate-100 px-1.5 py-1">
                      <p className="text-[8px] font-medium text-slate-500">{t("popup.rank")}</p>
                      <p className="font-semibold tabular-nums text-slate-950">
                        #{popupFeature.active_rank}
                      </p>
                    </div>
                  </div>
                )}
                <p className="mt-1 line-clamp-1 text-[9px] text-slate-500">
                  {popupFeature.arrondissement} ·{" "}
                  {popupFeature.code_iris ?? popupFeature.code_arrondissement}
                </p>
              </div>
            </Popup>
          ) : null}

          {selectedTransportPoint && transportPopup ? (
            <Popup
              anchor="bottom"
              closeButton
              closeOnClick={false}
              latitude={transportPopup.latitude}
              longitude={transportPopup.longitude}
              offset={10}
              onClose={() => {
                setSelectedTransportPoint(null);
                setTransportPopup(null);
              }}
            >
              <div className="max-w-[220px] p-1.5">
                <div className="flex items-center gap-2">
                  <span
                    className="grid h-7 w-7 place-items-center rounded-full text-[9px] font-bold text-white"
                    style={{
                      backgroundColor: getTransportMeta(selectedTransportPoint.type).color,
                    }}
                  >
                    {selectedTransportPoint.icon_label}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-[11px] font-semibold leading-snug text-slate-950">
                      {selectedTransportPoint.name}
                    </p>
                    <p className="text-[9px] font-semibold uppercase tracking-wide text-slate-500">
                      {selectedTransportPoint.display_type}
                    </p>
                  </div>
                </div>
                <div className="mt-1.5 rounded-lg bg-slate-100 px-1.5 py-1 text-[9px] text-slate-600">
                  Lat {selectedTransportPoint.lat.toFixed(5)} · Lng{" "}
                  {selectedTransportPoint.lng.toFixed(5)}
                </div>
              </div>
            </Popup>
          ) : null}
        </Map>
      </div>

      {mainIndicator === "housing" &&
      selectedMetric === "sale_score" &&
      saleTimeline &&
      selectedPeriod ? (
        <div className="pointer-events-auto absolute bottom-6 left-1/2 z-20 w-[min(92vw,520px)] -translate-x-1/2 rounded-2xl border border-slate-900/8 bg-white/95 px-4 py-3 shadow-[0_8px_32px_rgba(15,23,42,0.16)] backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <button
              type="button"
              aria-label={isPlaying ? t("a11y.pauseTimeline") : t("a11y.playTimeline")}
              onClick={() =>
                setIsPlaying((playing) => {
                  if (playing) return false;
                  const periods = saleTimeline.periods;
                  // Restart from the start if parked at the most recent quarter.
                  if (selectedPeriod === periods[periods.length - 1]) {
                    setSelectedPeriod(periods[0]);
                  }
                  return true;
                })
              }
              className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-slate-900 text-sm text-white hover:bg-slate-700"
            >
              {isPlaying ? "❚❚" : "►"}
            </button>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  {t("timeline.title")}
                </span>
                <span className="text-sm font-bold tabular-nums text-slate-900">
                  {formatQuarterLabel(selectedPeriod)}
                </span>
              </div>
              <input
                aria-label={t("a11y.timelineQuarter")}
                type="range"
                min={0}
                max={saleTimeline.periods.length - 1}
                value={Math.max(0, saleTimeline.periods.indexOf(selectedPeriod))}
                onChange={(event) => {
                  setIsPlaying(false);
                  setSelectedPeriod(saleTimeline.periods[Number(event.target.value)]);
                }}
                className="mt-1 w-full accent-slate-900"
              />
              <div className="flex justify-between text-[10px] font-medium text-slate-400">
                <span>{formatQuarterLabel(saleTimeline.periods[0])}</span>
                <span>
                  {formatQuarterLabel(
                    saleTimeline.periods[saleTimeline.periods.length - 1],
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <div
        className={`pointer-events-none absolute inset-x-0 bottom-0 top-[52px] z-10 flex flex-col justify-between gap-2 overflow-y-auto p-2.5 md:top-0 md:p-4 ${sidebarMapInsetClass}`}
      >
        <div
          aria-label={t("a11y.mapOptions")}
          className="pointer-events-auto fixed right-3 top-14 z-25 flex max-w-[min(calc(100vw-1.5rem),280px)] flex-wrap items-center justify-end gap-1.5 md:right-4 md:top-4"
        >
          <div
            aria-label="Language"
            className="flex items-center overflow-hidden rounded-full border border-slate-900/8 bg-white/95 text-[11px] font-semibold shadow-[0_2px_12px_rgba(15,23,42,0.12)] backdrop-blur-md"
            role="group"
          >
            {(["en", "fr"] as const).map((code) => (
              <button
                aria-pressed={lang === code}
                className={`px-2.5 py-1 transition ${
                  lang === code ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
                }`}
                key={code}
                onClick={() => setLang(code)}
                type="button"
              >
                {code.toUpperCase()}
              </button>
            ))}
          </div>
          <button
            className="rounded-full border border-slate-900/8 bg-white/95 px-2.5 py-1 text-[11px] font-semibold text-slate-800 shadow-[0_2px_12px_rgba(15,23,42,0.12)] backdrop-blur-md hover:bg-white"
            onClick={() => setUiHidden((v) => !v)}
            type="button"
          >
            {uiHidden ? t("ui.showUI") : t("ui.hideUI")}
          </button>
          {!uiHidden && !showLegend ? (
            <button
              className="rounded-full border border-slate-900/8 bg-white/95 px-2.5 py-1 text-[11px] font-semibold text-slate-700 shadow-[0_2px_12px_rgba(15,23,42,0.12)] backdrop-blur-md hover:bg-white"
              onClick={() => setShowLegend(true)}
              type="button"
            >
              {t("ui.scoreKey")}
            </button>
          ) : null}
          {!uiHidden && !showDetails ? (
            <button
              className="rounded-full border border-slate-900/8 bg-white/95 px-2.5 py-1 text-[11px] font-semibold text-slate-700 shadow-[0_2px_12px_rgba(15,23,42,0.12)] backdrop-blur-md hover:bg-white"
              onClick={() => setShowDetails(true)}
              type="button"
            >
              {t("ui.showDetails")}
            </button>
          ) : null}
        </div>

        <div className="flex flex-col gap-2 xl:flex-row xl:items-start xl:justify-between">
          <div className="flex flex-1 flex-col gap-1.5 md:pr-36 xl:pr-44">
            {!uiHidden && showTitleCard ? (
              <GlassCard className="pointer-events-auto max-w-xl rounded-2xl p-2.5 md:p-3">
                <div className="flex flex-wrap items-center gap-1">
                  <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.12em] text-emerald-700 ring-1 ring-emerald-600/15">
                    {t("app.title")}
                  </span>
                  <span className="rounded-full bg-white/70 px-2 py-0.5 text-[9px] font-medium text-slate-500 ring-1 ring-slate-900/5">
                    {metricLabel}
                  </span>
                  {(mainIndicator === "vivabilite" || mainIndicator === "transport") && arrData ? (
                    <span className="rounded-full bg-sky-50 px-2 py-0.5 text-[9px] font-medium text-sky-600 ring-1 ring-sky-600/15">
                      {currentZoom < ZOOM_BREAK ? t("title.zoomToArr") : t("title.zoomToIris")}
                    </span>
                  ) : null}
                </div>
                <div className="mt-1.5 flex flex-wrap items-end gap-1.5">
                  <h1 className="text-base font-semibold tracking-tight text-slate-950 md:text-lg">
                    {mainLabel} · Paris
                  </h1>
                  <div className="flex items-center gap-1">
                    <button
                      className="rounded-full border border-slate-900/8 bg-white/80 px-2 py-0.5 text-[10px] font-semibold text-slate-700 shadow-[0_2px_8px_rgba(15,23,42,0.06)] hover:bg-white"
                      onClick={() => setShowMapIntro((open) => !open)}
                      type="button"
                    >
                      {showMapIntro ? t("common.hide") : t("common.about")}
                    </button>
                    <button
                      aria-label={t("a11y.closeTitleCard")}
                      className="rounded-full px-1.5 py-0.5 text-[13px] font-medium leading-none text-slate-500 hover:bg-slate-100"
                      onClick={() => setShowTitleCard(false)}
                      type="button"
                    >
                      ×
                    </button>
                  </div>
                </div>
                {showMapIntro ? (
                  <p className="mt-1.5 max-w-xl text-[11px] leading-snug text-slate-600">
                    {t("intro.text")}
                  </p>
                ) : null}
                {transportError && mainIndicator === "transport" ? (
                  <p className="mt-2 rounded-xl bg-rose-50 px-2.5 py-1.5 text-[11px] font-semibold text-rose-700">
                    {t("error.transportUnavailable")} {transportError}
                  </p>
                ) : null}
              </GlassCard>
            ) : null}
            {!uiHidden && !showTitleCard ? (
              <button
                className="pointer-events-auto w-fit rounded-full border border-slate-900/8 bg-white/90 px-2.5 py-1 text-[11px] font-semibold text-slate-700 shadow-[0_2px_8px_rgba(15,23,42,0.06)]"
                onClick={() => setShowTitleCard(true)}
                type="button"
              >
                Info
              </button>
            ) : null}
          </div>

          <div
            className={`flex flex-col items-stretch gap-2 xl:items-end ${
              !uiHidden && showLegend ? "pt-10 xl:pt-11" : ""
            }`}
          >
            {!uiHidden && showLegend ? (
              <div className="pointer-events-auto w-full max-w-[220px] xl:w-60">
                <Legend
                  label={metricLabel}
                  onClose={() => setShowLegend(false)}
                  onShowHoverPreviewChange={setShowHoverPreview}
                  showHoverPreview={showHoverPreview}
                />
              </div>
            ) : null}
          </div>
        </div>

        <div
          className={`grid gap-2 xl:items-end ${
            showWeightStudio && !uiHidden
              ? "xl:grid-cols-[minmax(0,340px)_1fr_minmax(0,320px)]"
              : "xl:grid-cols-1"
          }`}
        >
          {showWeightStudio && !uiHidden ? (
            <div className="pointer-events-auto order-2 xl:order-1">
              <WeightPanel
                onChange={updateWeight}
                onPreset={setWeights}
                onRankingSelect={selectRankedZone}
                selectedMapId={selectedCode}
                topFeatures={stats.topFeatures}
                weights={weights}
              />
            </div>
          ) : null}
          {showWeightStudio && !uiHidden ? (
            <div className="pointer-events-none hidden min-h-0 xl:order-2 xl:block" aria-hidden />
          ) : null}
          <div
            className={`pointer-events-auto order-1 xl:order-3 ${
              showWeightStudio && !uiHidden
                ? ""
                : "xl:max-w-[320px] xl:justify-self-end"
            }`}
          >
            {!uiHidden && showDetails ? (
              <DetailsPanel
                averageScore={stats.averageScore}
                bdcomData={bdcomIrisData}
                dvfData={dvfIrisData}
                featureCount={stats.featureCount}
                irisDataLoading={irisDataLoading}
                mainIndicator={mainIndicator}
                onClose={() => {
                  setSelectedCode(null);
                  setPopup(null);
                }}
                onDismissPanel={() => setShowDetails(false)}
                priceLookup={priceLookup}
                selected={selected}
                selectedMetric={selectedMetric}
                topFeature={stats.topFeature}
                weights={weights}
              />
            ) : null}
          </div>
        </div>
      </div>

      {loadingStates[mainIndicator] ? (
        <div className="absolute inset-0 z-20 grid place-items-center bg-slate-950/25 p-6 backdrop-blur-sm">
          <GlassCard className="rounded-3xl p-5 text-center">
            <p className="text-[13px] font-semibold text-slate-950">{t("loading.mapData")}</p>
            <p className="mt-1.5 text-[13px] text-slate-500">
              {lang === "fr"
                ? `Récupération des polygones et des scores ${mainLabel.toLowerCase()}...`
                : `Fetching ${mainLabel.toLowerCase()} polygons and scores...`}
            </p>
          </GlassCard>
        </div>
      ) : null}

      {error ? (
        <div className="absolute inset-0 z-30 grid place-items-center bg-slate-950/70 p-6 backdrop-blur">
          <GlassCard className="max-w-lg rounded-3xl p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red-600">
              {t("error.mapUnavailable")}
            </p>
            <h2 className="mt-2 text-xl font-semibold text-slate-950">
              {t("error.mapUnavailableDesc")}
            </h2>
            <p className="mt-2 text-[13px] leading-5 text-slate-600">{error}</p>
            <div className="mt-3 rounded-xl bg-slate-100 p-3 font-mono text-[11px] text-slate-700">
              python run_pipeline.py --gold
              <br />
              python run_api.py
            </div>
          </GlassCard>
        </div>
      ) : null}
    </main>
  );
}

export function EnhancedMapDashboard() {
  return (
    <LanguageProvider>
      <EnhancedMapDashboardInner />
    </LanguageProvider>
  );
}
