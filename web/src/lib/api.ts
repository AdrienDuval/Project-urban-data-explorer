import type {
  IndicatorMapFeatureCollection,
  TransportPoint,
  VivabiliteFeatureCollection,
} from "@/types/map";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

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

export async function fetchTransportPoints(): Promise<TransportPoint[]> {
  const response = await fetch(`${API_URL}/indicators/transport/points`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<TransportPoint[]>;
}
