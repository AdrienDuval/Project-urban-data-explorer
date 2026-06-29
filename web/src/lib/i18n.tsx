"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type Lang = "en" | "fr";

const STORAGE_KEY = "ude_lang";

/**
 * Dashboard UI strings. Only strings that actually differ between English and
 * French are listed here — identical strings (Paris, Score, Delta, …) stay as
 * literals in the components. `t(key)` falls back to the key itself if missing,
 * which makes any un-translated string visible during testing.
 */
export const messages: Record<string, { en: string; fr: string }> = {
  // ── Pillars ─────────────────────────────────────────────────────────
  "pillar.school.label": { en: "Schools", fr: "Écoles" },
  "pillar.school.short": { en: "Schools", fr: "Écoles" },
  "pillar.school.desc": {
    en: "Access to schools near each IRIS zone.",
    fr: "Accès aux écoles près de chaque zone IRIS.",
  },
  "pillar.childcare.label": { en: "Childcare", fr: "Garde d'enfants" },
  "pillar.childcare.short": { en: "Childcare", fr: "Garde" },
  "pillar.childcare.desc": {
    en: "Crèches and early childhood access (neutral baseline, 5/10 for all zones).",
    fr: "Crèches et accueil de la petite enfance (base neutre, 5/10 pour toutes les zones).",
  },
  "pillar.safety.label": { en: "Safety", fr: "Sécurité" },
  "pillar.safety.short": { en: "Safety", fr: "Sécurité" },
  "pillar.safety.desc": {
    en: "Neighbourhood safety and security (neutral baseline, 5/10 for all zones).",
    fr: "Sécurité du quartier (base neutre, 5/10 pour toutes les zones).",
  },
  "pillar.healthcare.label": { en: "Healthcare", fr: "Santé" },
  "pillar.healthcare.short": { en: "Health", fr: "Santé" },
  "pillar.healthcare.desc": {
    en: "Hospitals plus pharmacy/medical services nearby.",
    fr: "Hôpitaux et services pharmaceutiques/médicaux à proximité.",
  },
  "pillar.environment.label": { en: "Environment", fr: "Environnement" },
  "pillar.environment.short": { en: "Env.", fr: "Env." },
  "pillar.environment.desc": {
    en: "Air, noise, and heat (neutral baseline, 5/10 for all zones).",
    fr: "Air, bruit et chaleur (base neutre, 5/10 pour toutes les zones).",
  },
  "pillar.transport.label": { en: "Transport", fr: "Transport" },
  "pillar.transport.short": { en: "Transit", fr: "Transit" },
  "pillar.transport.desc": {
    en: "Metro, rail, tram, bus, cableway, and Velib access.",
    fr: "Accès métro, RER/rail, tram, bus, funiculaire et Vélib.",
  },
  "pillar.services.label": { en: "Daily services", fr: "Services quotidiens" },
  "pillar.services.short": { en: "Services", fr: "Services" },
  "pillar.services.desc": {
    en: "Food, post, banks, culture, sport, and daily amenities.",
    fr: "Alimentation, poste, banques, culture, sport et commodités quotidiennes.",
  },
  "pillar.green.label": { en: "Green spaces", fr: "Espaces verts" },
  "pillar.green.short": { en: "Green", fr: "Verts" },
  "pillar.green.desc": {
    en: "Accessible green surface per resident.",
    fr: "Surface verte accessible par habitant.",
  },

  // ── Main indicators ─────────────────────────────────────────────────
  "main.vivabilite.label": { en: "Family livability", fr: "Vivabilité familiale" },
  "main.vivabilite.desc": {
    en: "Composite family suitability score and its pillars.",
    fr: "Score composite d'habitabilité familiale et ses piliers.",
  },
  "main.transport.label": { en: "Transport", fr: "Transport" },
  "main.transport.desc": {
    en: "Public transport accessibility and stop overlays.",
    fr: "Accessibilité des transports publics et superposition des arrêts.",
  },
  "main.thermal.label": { en: "Thermal comfort", fr: "Confort thermique" },
  "main.thermal.desc": {
    en: "Tree density and cooling-area comfort by IRIS.",
    fr: "Densité d'arbres et confort des zones de refroidissement par IRIS.",
  },
  "main.housing.label": { en: "Housing", fr: "Logement" },
  "main.housing.desc": {
    en: "Rent and sale affordability at arrondissement level.",
    fr: "Abordabilité des loyers et des ventes au niveau de l'arrondissement.",
  },
  "main.demographics.label": { en: "Demographics", fr: "Démographie" },
  "main.demographics.desc": {
    en: "Income, occupational status and social mix by IRIS.",
    fr: "Revenus, CSP et mixité sociale par IRIS.",
  },

  // ── Sub-metrics ─────────────────────────────────────────────────────
  "sub.official.label": { en: "Official score", fr: "Score officiel" },
  "sub.official.desc": {
    en: "Default composite from the pipeline weights.",
    fr: "Composite par défaut des poids du pipeline.",
  },
  "sub.connectivity.label": {
    en: "Essential connectivity & services",
    fr: "Connectivité essentielle et services",
  },
  "sub.connectivity.desc": {
    en: "Composite of transport, healthcare, and daily services access.",
    fr: "Composite d'accès aux transports, à la santé et aux services quotidiens.",
  },
  "sub.familymix.label": { en: "Family mix", fr: "Mix familial" },
  "sub.familymix.desc": {
    en: "Custom composite using your weights.",
    fr: "Composite personnalisé utilisant vos poids.",
  },
  "sub.accessibility.label": { en: "Accessibility score", fr: "Score d'accessibilité" },
  "sub.accessibility.desc": {
    en: "Weighted métro, rail, tram, bus, and Vélib access.",
    fr: "Accès pondéré au métro, RER/rail, tram, bus et Vélib.",
  },
  "sub.thermal.label": { en: "Thermal comfort", fr: "Confort thermique" },
  "sub.thermal.desc": {
    en: "Composite comfort score from trees and cooling areas.",
    fr: "Score de confort composite des arbres et des zones de refroidissement.",
  },
  "sub.treedensity.label": { en: "Tree density", fr: "Densité d'arbres" },
  "sub.treedensity.desc": {
    en: "Tree density score by IRIS.",
    fr: "Score de densité d'arbres par IRIS.",
  },
  "sub.cooling.label": { en: "Cooling areas", fr: "Zones de refroidissement" },
  "sub.cooling.desc": {
    en: "Share of cool green areas by IRIS.",
    fr: "Part des espaces verts frais par IRIS.",
  },
  "sub.proximity.label": { en: "Proximity score", fr: "Score de proximité" },
  "sub.proximity.desc": {
    en: "Proximity to cooling areas within 800m radius.",
    fr: "Proximité des zones de refroidissement dans un rayon de 800 m.",
  },
  "sub.rent.label": { en: "Rent affordability", fr: "Abordabilité des loyers" },
  "sub.rent.desc": {
    en: "Median rent €/m², inverted so higher means more affordable.",
    fr: "Loyer médian €/m², inversé pour que plus élevé signifie plus abordable.",
  },
  "sub.sale.label": { en: "Sale affordability", fr: "Abordabilité des ventes" },
  "sub.sale.desc": {
    en: "Median sale €/m², inverted so higher means more affordable.",
    fr: "Prix de vente médian €/m², inversé pour que plus élevé signifie plus abordable.",
  },
  "sub.revenus.label": { en: "Income", fr: "Revenus" },
  "sub.revenus.desc": {
    en: "Median income per IRIS, normalized 0-10.",
    fr: "Revenu médian par IRIS, normalisé 0-10.",
  },

  // ── Sidebar ─────────────────────────────────────────────────────────
  "sidebar.urbanData": { en: "Urban Data", fr: "Données urbaines" },
  "sidebar.explorer": { en: "Explorer", fr: "Explorateur" },
  "sidebar.subIndicators": { en: "Sub-indicators", fr: "Sous-indicateurs" },
  "sidebar.stopsToShow": { en: "Stops to show", fr: "Arrêts à afficher" },
  "sidebar.searchFilters": { en: "Search & filters", fr: "Recherche et filtres" },
  "sidebar.searchPlaceholder": {
    en: "Search IRIS, arrondissement...",
    fr: "Rechercher IRIS, arrondissement...",
  },
  "sidebar.allArr": { en: "All arrondissements", fr: "Tous les arrondissements" },
  "sidebar.minScore": { en: "Minimum score:", fr: "Score minimum :" },
  "sidebar.topMatches": { en: "Top matches", fr: "Meilleures correspondances" },
  "sidebar.noMatch": { en: "No matching zones.", fr: "Aucune zone correspondante." },
  "sidebar.mainIndicators": { en: "Main indicators", fr: "Indicateurs principaux" },
  "metric.avg": { en: "Avg", fr: "Moy" },

  // ── Panels / a11y ───────────────────────────────────────────────────
  "a11y.about": { en: "About", fr: "À propos de" },
  "a11y.collapsePanel": { en: "Collapse panel", fr: "Réduire le panneau" },
  "a11y.expandPanel": { en: "Expand panel", fr: "Développer le panneau" },
  "a11y.closePanel": { en: "Close panel", fr: "Fermer le panneau" },
  "a11y.closeLegend": { en: "Close legend", fr: "Fermer la légende" },
  "a11y.closeTitleCard": { en: "Close title card", fr: "Fermer la carte de titre" },
  "a11y.timelineQuarter": { en: "Timeline quarter", fr: "Trimestre de la chronologie" },
  "a11y.playTimeline": { en: "Play timeline", fr: "Lancer la chronologie" },
  "a11y.pauseTimeline": { en: "Pause timeline", fr: "Mettre en pause la chronologie" },
  "a11y.mapOptions": { en: "Map display options", fr: "Options d'affichage de la carte" },
  "mobile.indicatorsFilters": { en: "Indicators & filters", fr: "Indicateurs et filtres" },
  "common.close": { en: "Close", fr: "Fermer" },
  "common.hide": { en: "Hide", fr: "Masquer" },
  "common.about": { en: "About", fr: "À propos" },
  "common.noData": { en: "No data", fr: "Pas de données" },
  "common.na": { en: "N/A", fr: "S/O" },
  "common.loadingZone": { en: "Loading zone data...", fr: "Chargement des données de zone..." },

  // ── Legend ──────────────────────────────────────────────────────────
  "legend.lowToHigh": { en: "low to high", fr: "bas à haut" },
  "legend.hoverPreview": { en: "Hover preview", fr: "Aperçu au survol" },

  // ── Weight studio ───────────────────────────────────────────────────
  "weight.studio": { en: "Score studio", fr: "Studio de score" },
  "weight.choosePriorities": {
    en: "Choose your family priorities",
    fr: "Choisissez vos priorités familiales",
  },
  "weight.studioDesc": {
    en: "Scores update instantly. Higher school weight favors areas with stronger school accessibility.",
    fr: "Les scores se mettent à jour instantanément. Un poids d'école plus élevé favorise les zones ayant une meilleure accessibilité aux écoles.",
  },
  "weight.officialFamily": { en: "Official family score", fr: "Score familial officiel" },
  "weight.equalWeights": { en: "Equal weights", fr: "Poids égaux" },
  "weight.currentTop3": { en: "Current top 3", fr: "Top 3 actuel" },
  "weight.weightOf": { en: "weight", fr: "Poids de" },
  "score.weight": { en: "Weight", fr: "Poids" },
  "score.contribution": { en: "contribution", fr: "contribution" },
  "score.pillarScore": { en: "Pillar score (0–10)", fr: "Score du pilier (0–10)" },

  // ── Details panel ───────────────────────────────────────────────────
  "details.selectedArea": { en: "Selected area", fr: "Zone sélectionnée" },
  "details.bestMatch": { en: "Best current match", fr: "Meilleure correspondance actuelle" },
  "details.mappedZonesSuffix": { en: "mapped IRIS zones", fr: "zones IRIS cartographiées" },
  "details.dynamicRank": { en: "Dynamic rank", fr: "Classement dynamique" },
  "details.level": { en: "Level", fr: "Niveau" },
  "details.familyMixHint": {
    en: "Weighted average of the five pillars using your sliders. The map is colored by this headline score.",
    fr: "Moyenne pondérée des cinq piliers selon vos curseurs. La carte est colorée par ce score principal.",
  },
  "details.coloredHint": {
    en: "The map is colored by this score.",
    fr: "La carte est colorée par ce score.",
  },
  "details.original": { en: "Original", fr: "Original" },
  "details.delta": { en: "Delta", fr: "Delta" },
  "details.percentile": { en: "Percentile", fr: "Centile" },
  "details.irisCode": { en: "IRIS code", fr: "Code IRIS" },
  "details.zoneType": { en: "Zone type", fr: "Type de zone" },
  "details.arrCode": { en: "Arrondissement code", fr: "Code d'arrondissement" },
  "details.medianRent": { en: "Median rent", fr: "Loyer médian" },
  "details.medianSale": { en: "Median sale price", fr: "Prix de vente médian" },
  "details.strongestPillar": { en: "Strongest pillar", fr: "Pilier le plus fort" },
  "details.weakestPillar": { en: "Weakest pillar", fr: "Pilier le plus faible" },
  "details.coolingAreaScore": { en: "Cooling area score", fr: "Score de zone de refroidissement" },

  // ── Zone-type explanations ──────────────────────────────────────────
  "zone.activityNotScored": { en: "Activity zone — not scored", fr: "Zone d'activité — non notée" },
  "zone.specialNotScored": {
    en: "Special-use zone — not scored",
    fr: "Zone à usage spécial — non notée",
  },
  "zone.residentialGap": {
    en: "Residential zone — pipeline data gap",
    fr: "Zone résidentielle — lacune de données du pipeline",
  },
  "zone.activityDesc": {
    en: "This IRIS zone is classified by INSEE as an activity area (hospital campus, large offices, shopping centre, etc.). It has no permanent residential population, so liveability scoring does not apply.",
    fr: "Cette zone IRIS est classée par l'INSEE comme une zone d'activité (campus hospitalier, grands bureaux, centre commercial, etc.). Elle n'a pas de population résidentielle permanente, donc la notation d'habitabilité ne s'applique pas.",
  },
  "zone.specialDesc": {
    en: "This zone covers a park, river, cemetery, military area, or other non-residential land. INSEE does not publish household statistics for it.",
    fr: "Cette zone couvre un parc, une rivière, un cimetière, une zone militaire ou d'autres terres non résidentielles. L'INSEE ne publie pas de statistiques ménagères pour celle-ci.",
  },
  "zone.residentialDesc": {
    en: "This residential zone (TYP_IRIS = H) is present in the INSEE census but is missing from the pipeline output — likely due to a stale silver file. Re-run the pipeline to fix it.",
    fr: "Cette zone résidentielle (TYP_IRIS = H) est présente dans le recensement INSEE mais manque à la sortie du pipeline, probablement en raison d'un fichier silver obsolète. Réexécutez le pipeline pour le corriger.",
  },
  "zone.typeA": { en: "A — Activity", fr: "A — Activité" },
  "zone.typeD": { en: "D — Miscellaneous", fr: "D — Divers" },
  "zone.typeH": { en: "H — Residential", fr: "H — Habitat" },

  // ── Demographics labels ─────────────────────────────────────────────
  "demo.medianIncome": { en: "Median income", fr: "Revenu médian" },
  "demo.gini": { en: "Gini index", fr: "Indice de Gini" },
  "demo.executives": { en: "% executives", fr: "% cadres" },
  "demo.povertyRate": { en: "Poverty rate", fr: "Taux de pauvreté" },

  // ── Commerce & transactions ─────────────────────────────────────────
  "commerce.title": { en: "Commerce & Transactions", fr: "Commerce et transactions" },
  "commerce.establishments": { en: "Establishments", fr: "Établissements" },
  "commerce.avgSurface": { en: "Avg surface", fr: "Surface moyenne" },
  "commerce.topActivity": { en: "Top activity", fr: "Activité principale" },
  "commerce.noCommercial": {
    en: "No commercial data for this zone",
    fr: "Aucune donnée commerciale pour cette zone",
  },
  "commerce.medianM2": { en: "Median €/m²", fr: "Médian €/m²" },
  "commerce.medianSurface": { en: "Median surface", fr: "Surface médiane" },
  "commerce.noTransaction": {
    en: "No transaction data for this zone",
    fr: "Aucune donnée de transaction pour cette zone",
  },

  // ── Map popup ───────────────────────────────────────────────────────
  "popup.selected": { en: "Selected", fr: "Sélectionné" },
  "popup.preview": { en: "Preview", fr: "Aperçu" },
  "popup.activityZone": { en: "⚙ Activity zone", fr: "⚙ Zone d'activité" },
  "popup.specialZone": { en: "🌿 Special-use zone", fr: "🌿 Zone à usage spécial" },
  "popup.residentialGap": { en: "⚠ Residential — data gap", fr: "⚠ Résidentiel — lacune de données" },
  "popup.activityDesc": {
    en: "Institutional or commercial area — no residential population scored.",
    fr: "Zone institutionnelle ou commerciale — aucune population résidentielle notée.",
  },
  "popup.specialDesc": {
    en: "Park, water body, or public space — no household data.",
    fr: "Parc, plan d'eau ou espace public — pas de données ménagères.",
  },
  "popup.residentialDesc": {
    en: "Residential zone missing from pipeline output. Re-run `python run_pipeline.py`.",
    fr: "Zone résidentielle manquante à la sortie du pipeline. Réexécutez `python run_pipeline.py`.",
  },
  "popup.rank": { en: "Rank", fr: "Classement" },

  // ── Timeline ────────────────────────────────────────────────────────
  "timeline.title": { en: "Median sale price by quarter", fr: "Prix de vente médian par trimestre" },

  // ── Top-bar controls ────────────────────────────────────────────────
  "ui.showUI": { en: "Show UI", fr: "Afficher l'interface" },
  "ui.hideUI": { en: "Hide UI", fr: "Masquer l'interface" },
  "ui.scoreKey": { en: "Score key", fr: "Clé de score" },
  "ui.showDetails": { en: "Show details", fr: "Afficher les détails" },

  // ── Title card / intro ──────────────────────────────────────────────
  "app.title": { en: "Urban Data Explorer", fr: "Explorateur de données urbaines" },
  "title.zoomToArr": {
    en: "Arrondissements · zoom in for IRIS detail",
    fr: "Arrondissements · zoomez pour le détail IRIS",
  },
  "title.zoomToIris": {
    en: "IRIS zones · zoom out for arrondissements",
    fr: "Zones IRIS · dézoomez pour les arrondissements",
  },
  "intro.text": {
    en: "Choose a main indicator, then inspect its sub-indicators. Family livability combines family pillars, Transport adds project stop data, Thermal comfort maps trees and cooling areas, and Housing shows affordability by arrondissement.",
    fr: "Choisissez un indicateur principal, puis inspectez ses sous-indicateurs. Vivabilité familiale combine les piliers familiaux, Transport ajoute les données d'arrêt du projet, Confort thermique cartographie les arbres et les zones de refroidissement, et Logement affiche l'abordabilité par arrondissement.",
  },

  // ── Loading / error states ──────────────────────────────────────────
  "error.transportUnavailable": {
    en: "Transport points unavailable:",
    fr: "Points de transport indisponibles :",
  },
  "loading.mapData": { en: "Loading map data", fr: "Chargement des données de la carte" },
  "error.mapUnavailable": { en: "Map data unavailable", fr: "Données de carte indisponibles" },
  "error.mapUnavailableDesc": {
    en: "Start the API and generate the gold indicators first",
    fr: "Démarrez l'API et générez d'abord les indicateurs gold",
  },
};

export type MessageKey = keyof typeof messages;

type I18nContextValue = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  // Read the persisted choice after mount (avoids SSR/client mismatch).
  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "fr") {
      setLangState(stored);
    }
  }, []);

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    window.localStorage.setItem(STORAGE_KEY, next);
  }, []);

  const t = useCallback(
    (key: string) => messages[key]?.[lang] ?? key,
    [lang],
  );

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within a LanguageProvider");
  }
  return ctx;
}
