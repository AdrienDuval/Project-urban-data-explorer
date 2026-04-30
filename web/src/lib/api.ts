import type {
  BdcomIrisStats,
  DvfIrisStats,
  IndicatorMapFeatureCollection,
  TransportPoint,
  VivabiliteFeatureCollection,
} from "@/types/map";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = window.localStorage.getItem("ude_auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const ANALYTICS_USER_KEY = "ude_analytics_user";

/** Stable anonymous id for MongoDB analytics (stored in localStorage). */
export function getAnalyticsUserKey(): string {
  if (typeof window === "undefined") {
    return "";
  }
  let key = window.localStorage.getItem(ANALYTICS_USER_KEY);
  if (!key) {
    key = crypto.randomUUID();
    window.localStorage.setItem(ANALYTICS_USER_KEY, key);
  }
  return key;
}

export type ZoneClickPayload = {
  user_key: string;
  zone_id: string;
  zone_name?: string | null;
  geography?: string | null;
};

/** Records a zone polygon click (fire-and-forget; failures are ignored). */
export function recordZoneClick(payload: ZoneClickPayload): void {
  const { user_key, zone_id, zone_name, geography } = payload;
  void fetch(`${API_URL}/analytics/zone-clicks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_key,
      zone_id,
      zone_name: zone_name ?? undefined,
      geography: geography ?? undefined,
    }),
  }).catch(() => {
    /* analytics must not break the map */
  });
}

export type ZoneTotalRow = {
  zone_id: string;
  total_clicks: number;
  zone_name?: string | null;
  geography?: string | null;
};

/** Most-clicked zones across all visitors (needs ``MONGO_URI`` on the API). */
export async function fetchTopZonesByClicks(limit = 50): Promise<ZoneTotalRow[]> {
  const response = await fetch(
    `${API_URL}/analytics/zone-clicks/zones/top?limit=${limit}`,
    { cache: "no-store" },
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const data = (await response.json()) as { zones: ZoneTotalRow[] };
  return data.zones;
}

export type UserZoneInterestRow = {
  user_key: string;
  zone_id: string;
  clicks: number;
  zone_name?: string | null;
  geography?: string | null;
};

/** Zones a given anonymous ``user_key`` clicked most often. */
export async function fetchUserZoneInterests(
  userKey: string,
  limit = 50,
): Promise<UserZoneInterestRow[]> {
  const enc = encodeURIComponent(userKey);
  const response = await fetch(
    `${API_URL}/analytics/zone-clicks/users/${enc}?limit=${limit}`,
    { cache: "no-store" },
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const data = (await response.json()) as { interests: UserZoneInterestRow[] };
  return data.interests;
}

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

export async function fetchVivabiliteMap(): Promise<VivabiliteFeatureCollection> {
  const response = await fetch(`${API_URL}/map/vivabilite-familiale`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<VivabiliteFeatureCollection>;
}

export async function fetchVivabiliteArrondissement(): Promise<VivabiliteFeatureCollection> {
  const response = await fetch(`${API_URL}/map/vivabilite-familiale/arrondissement`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<VivabiliteFeatureCollection>;
}

export async function fetchThermalComfortMap(): Promise<IndicatorMapFeatureCollection> {
  const response = await fetch(`${API_URL}/map/thermal-comfort`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<IndicatorMapFeatureCollection>;
}

export async function fetchRentMap(): Promise<IndicatorMapFeatureCollection> {
  const response = await fetch(`${API_URL}/map/housing/rent`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<IndicatorMapFeatureCollection>;
}

export async function fetchSaleMap(): Promise<IndicatorMapFeatureCollection> {
  const response = await fetch(`${API_URL}/map/housing/sale`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<IndicatorMapFeatureCollection>;
}

export async function fetchBdcomByIris(codeIris: string): Promise<BdcomIrisStats> {
  const response = await fetch(
    `${API_URL}/bdcom/by-iris/${encodeURIComponent(codeIris)}`,
    { cache: "no-store" },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<BdcomIrisStats>;
}

export async function fetchDvfByIris(codeIris: string): Promise<DvfIrisStats> {
  const response = await fetch(
    `${API_URL}/dvf/by-iris/${encodeURIComponent(codeIris)}`,
    { cache: "no-store" },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<DvfIrisStats>;
}

export async function fetchTransportPoints(): Promise<TransportPoint[]> {
  const response = await fetch(`${API_URL}/indicators/transport/points`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<TransportPoint[]>;
}


export async function fetchDemographicsMap(): Promise<IndicatorMapFeatureCollection> {
  const response = await fetch(`${API_URL}/map/demographics`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<IndicatorMapFeatureCollection>;
}