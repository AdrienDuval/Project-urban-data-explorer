"use client";

import type { Feature, FeatureCollection, Geometry } from "geojson";
import { useEffect, useMemo, useState } from "react";
import Map, {
  Layer,
  Popup,
  Source,
  type LayerProps,
  type MapMouseEvent,
  type ViewState,
} from "react-map-gl/mapbox";

import { fetchTransportPoints, fetchVivabiliteMap } from "@/lib/api";
import type {
  TransportPoint,
  TransportPointFeatureCollection,
  TransportPointProperties,
  TransportType,
  VivabiliteFeatureCollection,
  VivabiliteProperties,
} from "@/types/map";

type WeightKey =
  | "school_score"
  | "childcare_score"
  | "safety_score"
  | "healthcare_score"
  | "environment_score"
  | "transport_score"
  | "daily_services_score"
  | "green_spaces_score";

type MetricKey = "family_mix" | WeightKey;

type Weights = Record<WeightKey, number>;

type ComputedProperties = VivabiliteProperties & {
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

const initialViewState: Partial<ViewState> = {
  longitude: 2.3522,
  latitude: 48.8566,
  zoom: 11.45,
  pitch: 0,
  bearing: 0,
};

const parisMaxBounds: [[number, number], [number, number]] = [
  [2.22, 48.8],
  [2.48, 48.92],
];

const defaultWeights: Weights = {
  school_score: 20,
  childcare_score: 15,
  safety_score: 20,
  healthcare_score: 15,
  environment_score: 15,
  green_spaces_score: 7.5,
  transport_score: 5,
  daily_services_score: 2.5,
};

const equalWeights: Weights = {
  school_score: 12.5,
  childcare_score: 12.5,
  safety_score: 12.5,
  healthcare_score: 12.5,
  environment_score: 12.5,
  green_spaces_score: 12.5,
  transport_score: 12.5,
  daily_services_score: 12.5,
};

const pillarMeta: Array<{
  key: WeightKey;
  label: string;
  shortLabel: string;
  description: string;
  color: string;
}> = [
  {
    key: "school_score",
    label: "Schools",
    shortLabel: "Schools",
    description: "Access to schools near each IRIS zone.",
    color: "#2563eb",
  },
  {
    key: "childcare_score",
    label: "Childcare",
    shortLabel: "Childcare",
    description: "Crèches and early childhood access (neutral baseline, 5/10 for all zones).",
    color: "#db2777",
  },
  {
    key: "safety_score",
    label: "Safety",
    shortLabel: "Safety",
    description: "Neighbourhood safety and security (neutral baseline, 5/10 for all zones).",
    color: "#dc2626",
  },
  {
    key: "healthcare_score",
    label: "Healthcare",
    shortLabel: "Health",
    description: "Hospitals plus pharmacy/medical services nearby.",
    color: "#0891b2",
  },
  {
    key: "environment_score",
    label: "Environment",
    shortLabel: "Env.",
    description: "Air, noise, and heat (neutral baseline, 5/10 for all zones).",
    color: "#65a30d",
  },
  {
    key: "transport_score",
    label: "Transport",
    shortLabel: "Transit",
    description: "Metro, rail, tram, bus, cableway, and Velib access.",
    color: "#7c3aed",
  },
  {
    key: "daily_services_score",
    label: "Daily services",
    shortLabel: "Services",
    description: "Food, post, banks, culture, sport, and daily amenities.",
    color: "#ea580c",
  },
  {
    key: "green_spaces_score",
    label: "Green spaces",
    shortLabel: "Green",
    description: "Accessible green surface per resident.",
    color: "#16a34a",
  },
];

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

const metricOptions: Array<{
  key: MetricKey;
  label: string;
  description: string;
}> = [
  {
    key: "family_mix",
    label: "Family mix",
    description: "Custom composite using your weights.",
  },
  {
    key: "school_score",
    label: "Schools",
    description: "School accessibility only.",
  },
  {
    key: "childcare_score",
    label: "Childcare",
    description: "Early childhood access (flat 5/10 baseline for all zones).",
  },
  {
    key: "safety_score",
    label: "Safety",
    description: "Neighbourhood safety (flat 5/10 baseline for all zones).",
  },
  {
    key: "healthcare_score",
    label: "Healthcare",
    description: "Hospitals, pharmacies, and medical services.",
  },
  {
    key: "environment_score",
    label: "Environment",
    description: "Environmental quality (flat 5/10 baseline for all zones).",
  },
  {
    key: "transport_score",
    label: "Transport",
    description: "Public transport and Velib access.",
  },
  {
    key: "daily_services_score",
    label: "Daily services",
    description: "Food, post, banks, culture, sport, and everyday amenities.",
  },
  {
    key: "green_spaces_score",
    label: "Green spaces",
    description: "Accessible green space per resident.",
  },
];

const fillLayer: LayerProps = {
  id: "vivabilite-fill",
  type: "fill",
  paint: {
    "fill-color": [
      "interpolate",
      ["linear"],
      ["coalesce", ["get", "active_score"], 0],
      0,
      "#f43f5e",
      2,
      "#fb923c",
      4,
      "#fbbf24",
      6,
      "#a3e635",
      8,
      "#22c55e",
      10,
      "#047857",
    ],
    "fill-opacity": [
      "interpolate",
      ["linear"],
      ["zoom"],
      9,
      0.58,
      13,
      0.78,
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

function clampWeight(value: number) {
  return Math.max(0, Math.min(100, value));
}

function effectiveWeight(weights: Weights, key: WeightKey) {
  const total = Object.values(weights).reduce((sum, weight) => sum + weight, 0);
  return total > 0 ? weights[key] / total : 0;
}

function calculateWeightedScore(properties: VivabiliteProperties, weights: Weights) {
  let weightedSum = 0;
  let availableWeight = 0;

  for (const pillar of pillarMeta) {
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
  properties: VivabiliteProperties,
  weightedScore: number | null,
  metric: MetricKey,
) {
  if (metric === "family_mix") {
    return weightedScore;
  }

  const value = properties[metric];
  return typeof value === "number" ? value : null;
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
  data: VivabiliteFeatureCollection | null,
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

function GlassCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`border border-white/65 bg-white/82 shadow-[0_24px_80px_rgba(15,23,42,0.18)] ring-1 ring-slate-900/5 backdrop-blur-2xl ${className}`}
    >
      {children}
    </div>
  );
}

function Metric({
  label,
  value,
  tone = "light",
}: {
  label: string;
  value: string;
  tone?: "light" | "dark" | "green";
}) {
  const styles = {
    light: "bg-white/70 text-slate-950",
    dark: "bg-slate-950 text-white",
    green: "bg-emerald-600 text-white",
  };

  return (
    <div className={`rounded-[1.4rem] p-4 ${styles[tone]}`}>
      <p className="text-xs font-medium opacity-70">{label}</p>
      <p className="mt-1 text-2xl font-bold tracking-tight">{value}</p>
    </div>
  );
}

function Sidebar({
  featureCount,
  averageScore,
  schoolShare,
  selectedMetric,
  transportTypeCounts,
  visibleTransportTypes,
  onMetricChange,
  onTransportTypeToggle,
}: {
  featureCount: number;
  averageScore: number | null;
  schoolShare: number;
  selectedMetric: MetricKey;
  transportTypeCounts: Record<TransportType, number>;
  visibleTransportTypes: Record<TransportType, boolean>;
  onMetricChange: (metric: MetricKey) => void;
  onTransportTypeToggle: (type: TransportType) => void;
}) {
  const showTransportFilters = selectedMetric === "transport_score";

  return (
    <aside className="pointer-events-auto flex max-h-[190px] shrink-0 flex-col overflow-y-auto border-white/70 bg-white/88 shadow-[18px_0_70px_rgba(15,23,42,0.14)] ring-1 ring-slate-900/5 backdrop-blur-2xl md:h-screen md:max-h-screen md:w-72 md:border-r">
      <div className="flex items-center justify-between border-b border-slate-200/70 px-5 py-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-emerald-700">
            Urban Data
          </p>
          <h1 className="mt-1 text-xl font-bold tracking-tight text-slate-950">
            Explorer
          </h1>
        </div>
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
          Paris
        </span>
      </div>

      <div className="space-y-2 px-4 pb-2 pt-4">
        <p className="px-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
          Map indices
        </p>
        {metricOptions.map((metric) => {
          const active = selectedMetric === metric.key;

          return (
            <button
              className={`w-full rounded-2xl px-3 py-3 text-left transition ${
                active
                  ? "bg-emerald-600 text-white shadow-lg shadow-emerald-900/20"
                  : "bg-white/55 text-slate-600 hover:bg-slate-100"
              }`}
              key={metric.key}
              onClick={() => onMetricChange(metric.key)}
              type="button"
            >
              <span className="block text-sm font-bold">{metric.label}</span>
              <span
                className={`mt-0.5 block text-xs ${
                  active ? "text-emerald-50" : "text-slate-400"
                }`}
              >
                {metric.description}
              </span>
            </button>
          );
        })}
      </div>

      {showTransportFilters ? (
        <div className="space-y-2 px-4 pb-4">
          <p className="px-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            Stops to show
          </p>
          {transportTypes.map((transport) => {
            const active = visibleTransportTypes[transport.type];

            return (
              <button
                className={`flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition ${
                  active ? "bg-white text-slate-900" : "bg-white/35 text-slate-400"
                }`}
                key={transport.type}
                onClick={() => onTransportTypeToggle(transport.type)}
                type="button"
              >
                <span
                  className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-[10px] font-black text-white"
                  style={{ backgroundColor: transport.color }}
                >
                  {transport.icon}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-bold">{transport.label}</span>
                  <span className="block text-xs text-slate-400">
                    {formatNumber(transportTypeCounts[transport.type] ?? 0)} points
                  </span>
                </span>
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    active ? "bg-emerald-500" : "bg-slate-300"
                  }`}
                />
              </button>
            );
          })}
        </div>
      ) : null}

      <div className="grid grid-cols-3 gap-2 border-t border-slate-200/70 p-4 md:mt-auto md:block md:space-y-2">
        <Metric label="Zones" value={formatNumber(featureCount)} />
        <Metric label="Avg" value={formatScore(averageScore)} />
        <Metric label="Schools" value={`${schoolShare}%`} />
      </div>
    </aside>
  );
}

function Legend() {
  const stops = [
    { label: "0", color: "#f43f5e" },
    { label: "2", color: "#fb923c" },
    { label: "4", color: "#fbbf24" },
    { label: "6", color: "#a3e635" },
    { label: "8", color: "#22c55e" },
    { label: "10", color: "#047857" },
  ];

  return (
    <GlassCard className="rounded-[1.6rem] p-4">
      <div className="mb-3 flex items-center justify-between gap-4">
        <p className="text-sm font-semibold text-slate-950">Liveability score</p>
        <p className="text-xs font-medium text-slate-500">low to high</p>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-linear-to-r from-rose-500 via-amber-300 to-emerald-700" />
      <div className="mt-2 flex justify-between text-[11px] font-medium text-slate-500">
        {stops.map((stop) => (
          <span key={stop.label} className="flex items-center gap-1">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: stop.color }}
            />
            {stop.label}
          </span>
        ))}
      </div>
    </GlassCard>
  );
}

function WeightPanel({
  weights,
  topFeatures,
  onChange,
  onPreset,
}: {
  weights: Weights;
  topFeatures: ComputedFeature[];
  onChange: (key: WeightKey, value: number) => void;
  onPreset: (weights: Weights) => void;
}) {
  const total = Object.values(weights).reduce((sum, weight) => sum + weight, 0);

  return (
    <GlassCard className="max-h-[min(62vh,680px)] overflow-y-auto rounded-4xl p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700">
            Score studio
          </p>
          <h2 className="mt-2 text-xl font-bold tracking-tight text-slate-950">
            Choose your family priorities
          </h2>
          <p className="mt-1 text-sm leading-5 text-slate-500">
            Scores update instantly. Higher school weight favors areas with
            stronger school accessibility.
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          className="rounded-full bg-slate-950 px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-800"
          onClick={() => onPreset(defaultWeights)}
          type="button"
        >
          Official family score
        </button>
        <button
          className="rounded-full border border-slate-200 bg-white/70 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-white"
          onClick={() => onPreset(equalWeights)}
          type="button"
        >
          Equal weights
        </button>
      </div>

      <div className="mt-5 space-y-4">
        {pillarMeta.map((pillar) => {
          const share = total > 0 ? Math.round((weights[pillar.key] / total) * 100) : 0;

          return (
            <div key={pillar.key}>
              <div className="mb-2 flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{pillar.label}</p>
                  <p className="text-xs text-slate-500">{pillar.description}</p>
                </div>
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-700">
                  {share}%
                </span>
              </div>
              <input
                aria-label={`${pillar.label} weight`}
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

      <div className="mt-5 rounded-[1.4rem] bg-slate-950 p-4 text-white">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
          Current top 3
        </p>
        <div className="mt-3 space-y-3">
          {topFeatures.map((feature) => (
            <div
              className="flex items-center justify-between gap-3"
              key={feature.properties.code_iris}
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">
                  #{feature.properties.active_rank} {feature.properties.name}
                </p>
                <p className="truncate text-xs text-slate-400">
                  {feature.properties.arrondissement}
                </p>
              </div>
              <p className="text-sm font-bold">
                {formatScore(feature.properties.active_score)}
              </p>
            </div>
          ))}
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
  return (
    <div className="space-y-3">
      {pillarMeta.map((pillar) => {
        const score = feature[pillar.key];
        const share = effectiveWeight(weights, pillar.key);
        const contribution =
          typeof score === "number" ? Number((score * share).toFixed(2)) : null;

        return (
          <div key={pillar.key} className="rounded-[1.2rem] bg-slate-100/80 p-3">
            <div className="mb-2 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-900">{pillar.shortLabel}</p>
                <p className="text-xs text-slate-500">
                  {showWeightContributions ? (
                    <>
                      Weight {Math.round(share * 100)}% · contribution{" "}
                      {formatScore(contribution)}
                    </>
                  ) : (
                    <>Pillar score (0–10)</>
                  )}
                </p>
              </div>
              <p className="text-sm font-bold text-slate-950">{formatScore(score)}</p>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white">
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
  selectedMetric,
  onClose,
}: {
  selected: ComputedProperties | null;
  topFeature: ComputedFeature | null;
  averageScore: number | null;
  featureCount: number;
  weights: Weights;
  selectedMetric: MetricKey;
  onClose: () => void;
}) {
  const feature = selected ?? topFeature?.properties ?? null;
  const metricLabel =
    metricOptions.find((metric) => metric.key === selectedMetric)?.label ?? "Score";
  const bestPillar = feature
    ? pillarMeta
        .map((pillar) => ({ ...pillar, value: feature[pillar.key] }))
        .filter((pillar) => typeof pillar.value === "number")
        .sort((a, b) => (b.value ?? 0) - (a.value ?? 0))[0]
    : null;
  const weakestPillar = feature
    ? pillarMeta
        .map((pillar) => ({ ...pillar, value: feature[pillar.key] }))
        .filter((pillar) => typeof pillar.value === "number")
        .sort((a, b) => (a.value ?? 0) - (b.value ?? 0))[0]
    : null;

  return (
    <GlassCard className="max-h-[min(70vh,760px)] w-full overflow-y-auto rounded-t-4xl p-5 md:w-[430px] md:rounded-4xl">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700">
            {selected ? "Selected IRIS" : "Best current match"}
          </p>
          <h2 className="mt-2 truncate text-2xl font-bold tracking-tight text-slate-950">
            {feature?.name ?? "Family liveability"}
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {feature?.arrondissement ?? `${featureCount} mapped IRIS zones`}
          </p>
        </div>
        {selected ? (
          <button
            className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-600 transition hover:bg-slate-200"
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        ) : null}
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <Metric
          label={metricLabel}
          tone="green"
          value={formatScore(feature?.active_score ?? averageScore)}
        />
        <Metric
          label="Dynamic rank"
          tone="dark"
          value={feature?.active_rank ? `#${feature.active_rank}` : "N/A"}
        />
      </div>

      <div className="mt-3 grid grid-cols-3 gap-3">
        <Metric
          label="Original"
          value={formatScore(feature?.vivabilite_score)}
        />
        <Metric
          label="Delta"
          value={
            typeof feature?.score_delta === "number"
              ? `${feature.score_delta >= 0 ? "+" : ""}${feature.score_delta.toFixed(1)}`
              : "N/A"
          }
        />
        <Metric
          label="Percentile"
          value={
            typeof feature?.active_percentile === "number"
              ? `${feature.active_percentile}%`
              : "N/A"
          }
        />
      </div>

      <div className="mt-4 rounded-[1.4rem] border border-slate-200/80 bg-white/55 p-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">Population</span>
          <span className="font-semibold text-slate-950">
            {formatNumber(feature?.population)}
          </span>
        </div>
        <div className="mt-3 flex items-center justify-between text-sm">
          <span className="text-slate-500">IRIS code</span>
          <span className="font-mono text-xs font-semibold text-slate-950">
            {feature?.code_iris ?? "N/A"}
          </span>
        </div>
      </div>

      {bestPillar && weakestPillar ? (
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="rounded-[1.2rem] bg-emerald-50 p-3">
            <p className="text-xs font-medium text-emerald-700">Strongest pillar</p>
            <p className="mt-1 text-sm font-bold text-slate-950">
              {bestPillar.shortLabel} · {formatScore(bestPillar.value)}
            </p>
          </div>
          <div className="rounded-[1.2rem] bg-rose-50 p-3">
            <p className="text-xs font-medium text-rose-700">Weakest pillar</p>
            <p className="mt-1 text-sm font-bold text-slate-950">
              {weakestPillar.shortLabel} · {formatScore(weakestPillar.value)}
            </p>
          </div>
        </div>
      ) : null}

      {feature ? (
        <div className="mt-4">
          <ScoreBreakdown
            feature={feature}
            showWeightContributions={selectedMetric === "family_mix"}
            weights={weights}
          />
        </div>
      ) : null}
    </GlassCard>
  );
}

export function EnhancedMapDashboard() {
  const [data, setData] = useState<VivabiliteFeatureCollection | null>(null);
  const [transportPoints, setTransportPoints] = useState<TransportPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [transportError, setTransportError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [weights, setWeights] = useState<Weights>(defaultWeights);
  const [selectedMetric, setSelectedMetric] = useState<MetricKey>("family_mix");
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
  const [showLegendPanel, setShowLegendPanel] = useState(false);

  useEffect(() => {
    let active = true;

    fetchVivabiliteMap()
      .then((geojson) => {
        if (!active) {
          return;
        }
        setData(geojson);
        setError(null);
      })
      .catch((err: Error) => {
        if (!active) {
          return;
        }
        setError(err.message);
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
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
  }, []);

  const displayData = useMemo(
    () => buildComputedGeojson(data, weights, selectedMetric),
    [data, selectedMetric, weights],
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
      topFeatures: topFeatures.slice(0, 3),
      featureCount: features.length,
    };
  }, [displayData]);

  const selected =
    displayData?.features.find((feature) => feature.properties.code_iris === selectedCode)
      ?.properties ?? null;
  const hovered =
    displayData?.features.find((feature) => feature.properties.code_iris === hoveredCode)
      ?.properties ?? null;
  const popupFeature = selected ?? hovered;
  const popupPosition = selected ? popup : hoverPopup;
  const activeCode = selectedCode ?? hoveredCode ?? "";
  const schoolShare = Math.round(effectiveWeight(weights, "school_score") * 100);
  const showTransportMarkers = selectedMetric === "transport_score";
  const showWeightStudio = selectedMetric === "family_mix";
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
    filter: ["==", ["get", "code_iris"], activeCode],
    paint: {
      "line-color": "#020617",
      "line-width": ["interpolate", ["linear"], ["zoom"], 10, 2, 14, 4],
      "line-opacity": activeCode ? 1 : 0,
    },
  };

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
    setHoveredCode(properties?.code_iris ?? null);
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

    setSelectedCode(properties.code_iris);
    setPopup({ longitude: event.lngLat.lng, latitude: event.lngLat.lat });
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
    <main className="relative min-h-screen overflow-hidden bg-[#f5f5f7] text-slate-950">
      <div className="absolute inset-x-0 top-0 z-20 md:bottom-0 md:left-0 md:right-auto">
        <Sidebar
          averageScore={stats.averageScore}
          featureCount={stats.featureCount}
          onMetricChange={changeMetric}
          onTransportTypeToggle={toggleTransportType}
          selectedMetric={selectedMetric}
          schoolShare={schoolShare}
          transportTypeCounts={transportTypeCounts}
          visibleTransportTypes={visibleTransportTypes}
        />
      </div>

      <div className="absolute inset-0 pt-[190px] md:left-72 md:pt-0">
        <Map
          initialViewState={initialViewState}
          interactiveLayerIds={[
            "vivabilite-fill",
            "transport-points",
            "transport-clusters",
          ]}
          mapStyle={mapStyle}
          mapboxAccessToken={mapboxToken}
          maxBounds={parisMaxBounds}
          maxZoom={20}
          minZoom={8.5}
          onClick={handleClick}
          onMouseLeave={handleMouseLeave}
          onMouseMove={handleMouseMove}
          reuseMaps
          style={{ height: "100%", width: "100%" }}
        >
          {displayData ? (
            <Source data={displayData} id="vivabilite-source" type="geojson">
              <Layer {...fillLayer} />
              <Layer {...outlineLayer} />
              <Layer {...activeLayer} />
            </Source>
          ) : null}

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
              offset={22}
              onClose={() => {
                setSelectedCode(null);
                setPopup(null);
              }}
            >
              <div className="min-w-64 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                  {selected ? "Selected area" : "Hover preview"}
                </p>
                <p className="mt-1 text-base font-bold text-slate-950">
                  {popupFeature.name}
                </p>
                <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                  <div className="rounded-2xl bg-emerald-50 p-2">
                    <p className="text-[11px] font-medium text-emerald-700">Score</p>
                    <p className="font-bold text-slate-950">
                      {formatScore(popupFeature.active_score)}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-100 p-2">
                    <p className="text-[11px] font-medium text-slate-500">Rank</p>
                    <p className="font-bold text-slate-950">
                      #{popupFeature.active_rank}
                    </p>
                  </div>
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  {popupFeature.arrondissement} · {popupFeature.code_iris}
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
              offset={18}
              onClose={() => {
                setSelectedTransportPoint(null);
                setTransportPopup(null);
              }}
            >
              <div className="min-w-64 p-3">
                <div className="flex items-center gap-3">
                  <span
                    className="grid h-10 w-10 place-items-center rounded-full text-xs font-black text-white"
                    style={{
                      backgroundColor: getTransportMeta(selectedTransportPoint.type).color,
                    }}
                  >
                    {selectedTransportPoint.icon_label}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-base font-bold text-slate-950">
                      {selectedTransportPoint.name}
                    </p>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      {selectedTransportPoint.display_type}
                    </p>
                  </div>
                </div>
                <div className="mt-3 rounded-2xl bg-slate-100 p-3 text-xs text-slate-600">
                  Lat {selectedTransportPoint.lat.toFixed(5)} · Lng{" "}
                  {selectedTransportPoint.lng.toFixed(5)}
                </div>
              </div>
            </Popup>
          ) : null}
        </Map>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 top-[190px] z-10 flex flex-col justify-between gap-4 overflow-y-auto p-4 md:left-72 md:top-0 md:p-6">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
          <GlassCard className="pointer-events-auto max-w-2xl rounded-3xl p-4 md:rounded-4xl md:p-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] text-emerald-700">
                Urban Data Explorer
              </span>
              <span className="rounded-full bg-white/70 px-3 py-1 text-xs font-semibold text-slate-500">
                {metricOptions.find((metric) => metric.key === selectedMetric)?.label ??
                  "Paris IRIS map"}
              </span>
            </div>
            <div className="mt-3 flex flex-wrap items-end gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-slate-950 md:text-4xl">
                Family liveability — Paris
              </h1>
              <button
                className="rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm hover:bg-white"
                onClick={() => setShowMapIntro((open) => !open)}
                type="button"
              >
                {showMapIntro ? "Hide" : "About"}
              </button>
            </div>
            {showMapIntro ? (
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 md:text-base">
                IRIS zones coloured by score. Choose an index in the sidebar, or
                Family mix to adjust pillar weights. Transport stops (métro, RER,
                tram, bus, Vélib) come from this project&apos;s data when you select
                Transport—not from the Mapbox basemap.
              </p>
            ) : null}
            {transportError && selectedMetric === "transport_score" ? (
              <p className="mt-2 rounded-2xl bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700">
                Transport points unavailable: {transportError}
              </p>
            ) : null}
          </GlassCard>

          <div className="flex items-start gap-2">
            <button
              className="pointer-events-auto rounded-full border border-slate-200/90 bg-white/90 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm backdrop-blur md:hidden"
              onClick={() => setShowLegendPanel((o) => !o)}
              type="button"
            >
              {showLegendPanel ? "Hide key" : "Score key"}
            </button>
            {showLegendPanel ? (
              <div className="pointer-events-auto w-72 max-w-[85vw] md:hidden">
                <Legend />
              </div>
            ) : null}
            <div className="pointer-events-auto hidden w-80 md:block">
              <Legend />
            </div>
          </div>
        </div>

        <div
          className={`grid gap-4 xl:items-end ${
            showWeightStudio
              ? "xl:grid-cols-[minmax(0,380px)_1fr_minmax(0,430px)]"
              : "xl:grid-cols-1"
          }`}
        >
          {showWeightStudio ? (
            <div className="pointer-events-auto order-2 xl:order-1">
              <WeightPanel
                onChange={updateWeight}
                onPreset={setWeights}
                topFeatures={stats.topFeatures}
                weights={weights}
              />
            </div>
          ) : null}
          {showWeightStudio ? (
            <div className="pointer-events-none hidden min-h-0 xl:order-2 xl:block" aria-hidden />
          ) : null}
          <div
            className={`pointer-events-auto order-1 xl:order-3 ${
              showWeightStudio ? "" : "xl:max-w-md xl:justify-self-end 2xl:max-w-[430px]"
            }`}
          >
            <DetailsPanel
              averageScore={stats.averageScore}
              featureCount={stats.featureCount}
              onClose={() => {
                setSelectedCode(null);
                setPopup(null);
              }}
              selected={selected}
              selectedMetric={selectedMetric}
              topFeature={stats.topFeature}
              weights={weights}
            />
          </div>
        </div>
      </div>

      {loading ? (
        <div className="absolute inset-0 z-20 grid place-items-center bg-slate-950/25 p-6 backdrop-blur-sm">
          <GlassCard className="rounded-4xl p-6 text-center">
            <p className="text-sm font-semibold text-slate-950">Loading map data</p>
            <p className="mt-2 text-sm text-slate-500">
              Fetching IRIS polygons and liveability scores...
            </p>
          </GlassCard>
        </div>
      ) : null}

      {error ? (
        <div className="absolute inset-0 z-30 grid place-items-center bg-slate-950/70 p-6 backdrop-blur">
          <GlassCard className="max-w-lg rounded-4xl p-6">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-red-600">
              Map data unavailable
            </p>
            <h2 className="mt-2 text-2xl font-bold text-slate-950">
              Start the API and generate the gold indicator first
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{error}</p>
            <div className="mt-4 rounded-2xl bg-slate-100 p-4 font-mono text-xs text-slate-700">
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
