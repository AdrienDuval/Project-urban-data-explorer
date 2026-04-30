import type { Feature, FeatureCollection, Geometry } from "geojson";

export type VivabiliteProperties = {
  map_id?: string | null;
  geography?: "iris" | "arrondissement" | null;
  code_iris: string;
  name: string | null;
  arrondissement: string | null;
  quarter_code: string | number | null;
  population: number | null;
  school_count?: number | null;
  schools_per_1000?: number | null;
  school_score: number | null;
  childcare_score?: number | null;
  safety_score?: number | null;
  healthcare_hospital_count?: number | null;
  healthcare_service_count?: number | null;
  weighted_healthcare_access?: number | null;
  healthcare_score?: number | null;
  environment_score?: number | null;
  transport_score: number | null;
  stop_count?: number | null;
  weighted_stops?: number | null;
  services_score: number | null;
  daily_service_count?: number | null;
  weighted_daily_service_count?: number | null;
  daily_services_score?: number | null;
  interior_m2?: number | null;
  adjacent_m2?: number | null;
  total_green_m2?: number | null;
  green_m2_per_resident?: number | null;
  green_spaces_score: number | null;
  essential_connectivity_score?: number | null;
  essential_connectivity_rank?: number | null;
  essential_connectivity_weights?: string | null;
  vivabilite_score: number | null;
  vivabilite_rank: number | null;
  vivabilite_model?: string | null;
  vivabilite_weights?: string | null;
};

export type IndicatorMapProperties = Partial<VivabiliteProperties> & {
  map_id?: string | null;
  geography?: "iris" | "arrondissement" | null;
  code_iris?: string | null;
  code_arrondissement?: string | null;
  name: string | null;
  arrondissement: string | null;
  thermal_score?: number | null;
  tree_density_score?: number | null;
  cooling_area_score?: number | null;
  indice_confort_thermique?: number | null;
  densite_arbres?: number | null;
  ratio_fraicheur?: number | null;
  rent_score?: number | null;
  loyer_median_m2?: number | null;
  loyer_q1_m2?: number | null;
  loyer_q3_m2?: number | null;
  sale_score?: number | null;
  prix_m2?: number | null;
  Trimestre?: string | null;
  date_periode?: string | null;
};

export type VivabiliteFeature = Feature<Geometry, VivabiliteProperties>;

export type VivabiliteFeatureCollection = FeatureCollection<
  Geometry,
  VivabiliteProperties
>;

export type IndicatorMapFeature = Feature<Geometry, IndicatorMapProperties>;

export type IndicatorMapFeatureCollection = FeatureCollection<
  Geometry,
  IndicatorMapProperties
>;

export type TransportType = "bus" | "metro" | "rail" | "tram" | "velib";

export type TransportPoint = {
  id: string;
  name: string;
  type: TransportType;
  lat: number;
  lng: number;
};

export type TransportPointProperties = TransportPoint & {
  icon_label: string;
  display_type: string;
};

export type TransportPointFeature = Feature<
  Geometry,
  TransportPointProperties
>;

export type TransportPointFeatureCollection = FeatureCollection<
  Geometry,
  TransportPointProperties
>;

export type BdcomIrisStats = {
  code_iris: string;
  total_establishments: number;
  avg_surface_m2: number;
  top_activities: Array<{ activity: string; count: number }>;
  by_type?: Record<string, number>;
};

export type DvfIrisStats = {
  code_iris: string;
  total_transactions: number;
  median_prix_m2: number;
  median_surface_m2: number;
  total_value: number;
  price_range?: { min: number; max: number };
  by_year?: Record<string, number>;
  by_type?: Record<string, number>;
};
