"use client";

import { useEffect, useMemo, useState } from "react";
import Map, {
  Layer,
  Popup,
  Source,
  type LayerProps,
  type MapMouseEvent,
  type ViewState,
} from "react-map-gl/mapbox";

import { fetchVivabiliteMap } from "@/lib/api";
import type {
  VivabiliteFeature,
  VivabiliteFeatureCollection,
  VivabiliteProperties,
} from "@/types/map";

type InteractiveMapEvent = MapMouseEvent & {
  features?: Array<{ properties?: unknown }>;
};

const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
const mapStyle =
  process.env.NEXT_PUBLIC_MAP_STYLE_URL ??
  (mapboxToken
    ? "mapbox://styles/mapbox/light-v11"
    : "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json");

const initialViewState: Partial<ViewState> = {
  longitude: 2.3522,
  latitude: 48.8566,
  zoom: 11.1,
  pitch: 0,
  bearing: 0,
};

const fillLayer: LayerProps = {
  id: "vivabilite-fill",
  type: "fill",
  paint: {
    "fill-color": [
      "interpolate",
      ["linear"],
      ["coalesce", ["get", "vivabilite_score"], 0],
      0,
      "#ef4444",
      2,
      "#f97316",
      4,
      "#facc15",
      6,
      "#84cc16",
      8,
      "#22c55e",
      10,
      "#15803d",
    ],
    "fill-opacity": 0.72,
    "fill-outline-color": "rgba(15, 23, 42, 0.25)",
  },
};

const outlineLayer: LayerProps = {
  id: "vivabilite-outline",
  type: "line",
  paint: {
    "line-color": "rgba(15, 23, 42, 0.35)",
    "line-width": 0.5,
  },
};

function formatScore(value: number | null) {
  return typeof value === "number" ? `${value.toFixed(1)}/10` : "No data";
}

function formatNumber(value: number | null) {
  return typeof value === "number" ? Intl.NumberFormat("fr-FR").format(value) : "N/A";
}

function getFeatureProperties(event: InteractiveMapEvent) {
  return event.features?.[0]?.properties as VivabiliteProperties | undefined;
}

function Legend() {
  const stops = [
    { label: "0", color: "#ef4444" },
    { label: "2", color: "#f97316" },
    { label: "4", color: "#facc15" },
    { label: "6", color: "#84cc16" },
    { label: "8", color: "#22c55e" },
    { label: "10", color: "#15803d" },
  ];

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-4 shadow-xl shadow-slate-950/10 backdrop-blur">
      <div className="mb-3 flex items-center justify-between gap-4">
        <p className="text-sm font-semibold text-slate-950">Vivabilité score</p>
        <p className="text-xs text-slate-500">0 to 10</p>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-linear-to-r from-red-500 via-yellow-400 to-green-700" />
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
    </div>
  );
}

function ScoreBreakdown({ feature }: { feature: VivabiliteProperties }) {
  const items = [
    ["Schools", feature.school_score],
    ["Transport", feature.transport_score],
    ["Services", feature.services_score],
    ["Green spaces", feature.green_spaces_score],
  ] as const;

  return (
    <div className="grid grid-cols-2 gap-3">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-2xl bg-slate-100 p-3">
          <p className="text-xs font-medium text-slate-500">{label}</p>
          <p className="mt-1 text-lg font-semibold text-slate-950">
            {formatScore(value)}
          </p>
        </div>
      ))}
    </div>
  );
}

function DetailsPanel({
  selected,
  topFeature,
  averageScore,
  featureCount,
  onClose,
}: {
  selected: VivabiliteProperties | null;
  topFeature: VivabiliteFeature | null;
  averageScore: number | null;
  featureCount: number;
  onClose: () => void;
}) {
  const feature = selected ?? topFeature?.properties ?? null;

  return (
    <aside className="pointer-events-auto w-full rounded-t-3xl border border-slate-200/80 bg-white/95 p-5 shadow-2xl shadow-slate-950/15 backdrop-blur md:w-[400px] md:rounded-3xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-700">
            {selected ? "Selected IRIS" : "Paris overview"}
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
            {feature?.name ?? "Vivabilité familiale"}
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {feature?.arrondissement ?? `${featureCount} mapped IRIS zones`}
          </p>
        </div>
        {selected ? (
          <button
            className="rounded-full border border-slate-200 px-3 py-1 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        ) : null}
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="rounded-2xl bg-emerald-600 p-4 text-white">
          <p className="text-xs font-medium text-emerald-100">Score</p>
          <p className="mt-1 text-3xl font-bold">
            {formatScore(feature?.vivabilite_score ?? averageScore)}
          </p>
        </div>
        <div className="rounded-2xl bg-slate-950 p-4 text-white">
          <p className="text-xs font-medium text-slate-300">Rank</p>
          <p className="mt-1 text-3xl font-bold">
            {feature?.vivabilite_rank ? `#${feature.vivabilite_rank}` : "N/A"}
          </p>
        </div>
      </div>

      <div className="mt-4 rounded-2xl border border-slate-200 p-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">Population</span>
          <span className="font-semibold text-slate-950">
            {formatNumber(feature?.population ?? null)}
          </span>
        </div>
        <div className="mt-3 flex items-center justify-between text-sm">
          <span className="text-slate-500">IRIS code</span>
          <span className="font-mono text-xs font-semibold text-slate-950">
            {feature?.code_iris ?? "N/A"}
          </span>
        </div>
      </div>

      {feature ? (
        <div className="mt-4">
          <ScoreBreakdown feature={feature} />
        </div>
      ) : null}
    </aside>
  );
}

export function MapDashboard() {
  const [data, setData] = useState<VivabiliteFeatureCollection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [hoveredCode, setHoveredCode] = useState<string | null>(null);
  const [selected, setSelected] = useState<VivabiliteProperties | null>(null);
  const [popup, setPopup] = useState<{ longitude: number; latitude: number } | null>(
    null,
  );

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

  const stats = useMemo(() => {
    const features = data?.features ?? [];
    const scores = features
      .map((feature) => feature.properties.vivabilite_score)
      .filter((score): score is number => typeof score === "number");
    const averageScore =
      scores.length > 0
        ? scores.reduce((sum, score) => sum + score, 0) / scores.length
        : null;
    const topFeature =
      features.find((feature) => feature.properties.vivabilite_rank === 1) ?? null;

    return { averageScore, topFeature, featureCount: features.length };
  }, [data]);

  const activeCode = selected?.code_iris ?? hoveredCode ?? "";
  const activeLayer: LayerProps = {
    id: "vivabilite-active",
    type: "line",
    filter: ["==", ["get", "code_iris"], activeCode],
    paint: {
      "line-color": "#0f172a",
      "line-width": 2.5,
      "line-opacity": activeCode ? 1 : 0,
    },
  };

  function handleMouseMove(event: InteractiveMapEvent) {
    const properties = getFeatureProperties(event);
    event.target.getCanvas().style.cursor = properties ? "pointer" : "";
    setHoveredCode(properties?.code_iris ?? null);
  }

  function handleMouseLeave(event: InteractiveMapEvent) {
    event.target.getCanvas().style.cursor = "";
    setHoveredCode(null);
  }

  function handleClick(event: InteractiveMapEvent) {
    const properties = getFeatureProperties(event);
    if (!properties) {
      return;
    }

    setSelected(properties);
    setPopup({ longitude: event.lngLat.lng, latitude: event.lngLat.lat });
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-950">
      <div className="absolute inset-0">
        <Map
          initialViewState={initialViewState}
          interactiveLayerIds={["vivabilite-fill"]}
          mapStyle={mapStyle}
          mapboxAccessToken={mapboxToken}
          maxZoom={16}
          minZoom={9}
          onClick={handleClick}
          onMouseLeave={handleMouseLeave}
          onMouseMove={handleMouseMove}
          reuseMaps
          style={{ height: "100%", width: "100%" }}
        >
          {data ? (
            <Source data={data} id="vivabilite-source" type="geojson">
              <Layer {...fillLayer} />
              <Layer {...outlineLayer} />
              <Layer {...activeLayer} />
            </Source>
          ) : null}

          {selected && popup ? (
            <Popup
              anchor="bottom"
              closeButton={false}
              latitude={popup.latitude}
              longitude={popup.longitude}
              offset={18}
            >
              <div className="min-w-48 p-1">
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                  {selected.arrondissement}
                </p>
                <p className="mt-1 font-semibold text-slate-950">{selected.name}</p>
                <p className="mt-1 text-sm text-slate-600">
                  Score {formatScore(selected.vivabilite_score)}
                </p>
              </div>
            </Popup>
          ) : null}
        </Map>
      </div>

      <section className="pointer-events-none absolute inset-x-0 top-0 z-10 p-4 md:p-6">
        <div className="pointer-events-auto max-w-xl rounded-3xl border border-white/70 bg-white/95 p-5 shadow-2xl shadow-slate-950/15 backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700">
            Urban Data Explorer
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 md:text-4xl">
            Family liveability across Paris
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 md:text-base">
            Explore IRIS neighbourhoods colored by a composite score combining
            schools, transport, services, and green spaces.
          </p>
        </div>
      </section>

      <section className="pointer-events-none absolute inset-x-0 bottom-0 z-10 flex flex-col gap-4 p-4 md:inset-x-auto md:bottom-6 md:left-6 md:right-6 md:flex-row md:items-end md:justify-between md:p-0">
        <div className="pointer-events-auto md:w-80">
          <Legend />
        </div>
        <DetailsPanel
          averageScore={stats.averageScore}
          featureCount={stats.featureCount}
          onClose={() => {
            setSelected(null);
            setPopup(null);
          }}
          selected={selected}
          topFeature={stats.topFeature}
        />
      </section>

      {loading ? (
        <div className="absolute inset-0 z-20 grid place-items-center bg-slate-950/30 backdrop-blur-sm">
          <div className="rounded-3xl bg-white p-6 text-center shadow-2xl">
            <p className="text-sm font-semibold text-slate-950">Loading map data</p>
            <p className="mt-2 text-sm text-slate-500">Fetching IRIS polygons and scores...</p>
          </div>
        </div>
      ) : null}

      {error ? (
        <div className="absolute inset-0 z-30 grid place-items-center bg-slate-950/70 p-6 backdrop-blur">
          <div className="max-w-lg rounded-3xl bg-white p-6 shadow-2xl">
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
          </div>
        </div>
      ) : null}
    </main>
  );
}
