# Indicateur de Vivabilité Familiale — Documentation

**Réponse à la question : Où à Paris fait-il bon vivre en famille ?**

Score composite de 0 à 10 calculé par zone IRIS (~992 zones à Paris), combinant quatre sous-indicateurs indépendants pondérés à parts égales.

---

## Score final

```
Vivabilité Familiale = (Écoles × 0.25) + (Transport × 0.25) + (Services × 0.25) + (Espaces Verts × 0.25)
```

Chaque sous-score est normalisé 0–10 indépendamment (0 = pire zone de Paris, 10 = meilleure zone).  
Le score composite est donc aussi sur une échelle 0–10 sans normalisation supplémentaire.

---

## Architecture des données

```
BRONZE (fichiers bruts)         SILVER (nettoyé, fichiers only)        GOLD (scores + DB)
────────────────────────        ───────────────────────────────        ─────────────────────────────────────────
schools/*.xlsx              →   schools_merged.csv              ──→   schools_score_iris.csv   + DB: school_density
espaces_verts.geojson       →   espaces_verts_paris.geojson     ──→   green_spaces_score_iris.csv + DB: green_spaces_score
transport/arrets.csv        →   transport_arrets_paris.csv      ──→   transport_score_iris.csv + DB: transport_score
transport/velib.csv         →   velib_paris.csv                 ──┘
BDCOM_2023.csv              →   bdcom_paris_clean.csv           ──→   services_score_iris.csv  + DB: services_score
hospitals.csv               →   hospitals_paris_clean.csv       ──┘
                                                                       vivabilite_familiale_iris.csv + DB: vivabilite_familiale
```

---

## Pilier 1 — Écoles (25 %)

**Objectif** : Mesurer l'accessibilité aux établissements scolaires depuis chaque zone IRIS.

**Sources Bronze** :
- `indice_vivabilite_familiale/etablissements-scolaires-colleges.xlsx`
- `indice_vivabilite_familiale/etablissements-scolaires-ecoles-elementaires.xlsx`
- `indice_vivabilite_familiale/etablissements-scolaires-maternelles.xlsx`

**Pipeline** :
- Silver : `src/silver/schools.py` → `schools_merged.csv` (fusion des 3 fichiers, dédoublonnage, filtre Paris)
- Gold  : `src/gold/school_density.py` → compte les établissements dans un rayon de 500 m autour de chaque zone IRIS (buffer spatial Lambert-93), rapporté à la population

**Formule** :
```
schools_per_1000 = nb_écoles_500m / population × 1000
school_score = normaliser(schools_per_1000) sur [0, 10]
```

**Granularité** : IRIS (~992 zones)

---

## Pilier 2 — Transport (25 %)

**Objectif** : Mesurer l'accessibilité aux transports en commun et au vélib depuis chaque zone IRIS.

**Sources Bronze** :
- `transport_data/arrets.csv` — arrêts RATP/SNCF (métro, RER, bus, tram, câble)
- `transport_data/velib.csv` — stations Vélib

**Pipeline** :
- Silver : `src/transport.py` → `transport_arrets_paris.csv` + `velib_paris.csv`
  (filtre Paris via code postal/INSEE, extraction coordonnées, normalisation du type)
- Gold  : `src/gold/transport_score.py` → buffer 500 m par IRIS, jointure spatiale, somme pondérée

**Pondérations par type d'arrêt** (définies dans `src/config.py`) :

| Type | Poids | Raison |
|------|-------|--------|
| rail (RER/Transilien) | 1.2 | Connectivité maximale |
| metro | 1.0 | Transport urbain principal |
| tram | 0.7 | |
| cableway | 0.5 | |
| bus | 0.4 | Réseau dense mais moins impactant |
| velib | 0.3 | Mobilité douce |

**Formule** :
```
weighted_stops = Σ (nb_arrêts_type × poids_type) pour tous les types dans 500 m
transport_score = normaliser(weighted_stops) sur [0, 10]
```

**Granularité** : IRIS (~992 zones)

---

## Pilier 3 — Services (25 %)

**Objectif** : Mesurer la proximité aux services essentiels pour les familles (santé + services du quotidien).

**Sources Bronze** :
- `public_service_data/les_etablissements_hospitaliers_franciliens.csv` — hôpitaux IDF
- `public_service_data/BDCOM_2023.csv` + `BDCOM_2023_OD.xlsx` — commerces et services parisiens

**Pipeline** :
- Silver : `src/silver/hospitals.py` → `hospitals_paris_clean.csv` (filtre Paris, coordonnées WGS84)
- Silver : `src/silver/bdcom.py` → `bdcom_paris_clean.csv` (fusion BDCOM + dictionnaire activités)
- Gold  : `src/gold/services_score.py` → buffer 500 m par IRIS, jointure spatiale sur les deux sources

**Filtrage BDCOM** : catégories `niv8 ∈ {2, 4}` uniquement :
- `niv8 = 2` : Alimentaire (épiceries, supermarchés, boulangeries…)
- `niv8 = 4` : Service commercial (pharmacies, banques, La Poste, pressing…)

**Pondérations** :
- Hôpital : ×3 (importance critique pour les familles)
- Service BDCOM : ×1

**Formule** :
```
weighted_services = (nb_hôpitaux × 3) + (nb_services_bdcom × 1) dans 500 m
services_score = normaliser(weighted_services) sur [0, 10]
```

> **Note technique** : les coordonnées BDCOM (colonnes X, Y) sont en Lambert-93 (EPSG:2154) — elles sont utilisées directement sans conversion. Les coordonnées des hôpitaux (lat, lng) sont en WGS84 (EPSG:4326) et sont reprojetées en EPSG:2154 avant la jointure spatiale.

**Granularité** : IRIS (~992 zones)

---

## Pilier 4 — Espaces Verts (25 %)

**Objectif** : Mesurer la surface d'espaces verts accessibles par habitant, avec un bonus pour les espaces verts à proximité immédiate.

**Source Bronze** :
- `indice_vivabilite_familiale/espaces_verts.geojson` — 2 528 polygones, opendata Paris, EPSG:4326

**Pipeline** :
- Silver : `src/silver/green_spaces.py` → `espaces_verts_paris.geojson`
  - Filtre : `ouvert_ferme == 'Ouvert'`
  - Suppression des décorations sur la voie publique (jardinières, etc.)
  - Recalcul de `surface_totale_reelle` si manquante (depuis la géométrie en EPSG:2154)
- Gold  : `src/gold/green_spaces_score.py` → jointure spatiale par centroïdes

**Formule** :
```
Pour chaque zone IRIS :
  interior_m2  = Σ surface des espaces verts dont le centroïde est dans l'IRIS
  adjacent_m2  = Σ surface des espaces verts dont le centroïde est dans un buffer
                   de 300 m autour de l'IRIS mais pas à l'intérieur
  total_green_m2 = interior_m2 + 0.5 × adjacent_m2
  green_m2_per_resident = total_green_m2 / population
  green_spaces_score = normaliser(green_m2_per_resident) sur [0, 10]
```

> Le bonus 50 % pour les espaces verts adjacents reflète le fait qu'un parc à 200 m est accessible à pied mais contribue moins qu'un parc dans la zone même.

**Granularité** : IRIS (~992 zones)

---

## Score Composite

**Script** : `src/gold/vivabilite_familiale.py`  
**DB table** : `vivabilite_familiale`  
**Fichier Gold** : `data/gold/vivabilite_familiale_iris.csv`

**Colonnes de sortie** :

| Colonne | Type | Description |
|---------|------|-------------|
| `IRIS` | str(9) | Code INSEE IRIS (9 chiffres, zero-padded) |
| `code_iris` | str(9) | Identique à IRIS |
| `LIBCOM` | str | Libellé arrondissement (ex : "Paris 7e Arrondissement") |
| `LIBIRIS` | str | Nom de la zone IRIS |
| `GRD_QUART` | str | Code grand quartier |
| `population` | float | Population résidente (INSEE 2022) |
| `school_score` | float | Score écoles 0–10 |
| `transport_score` | float | Score transport 0–10 |
| `services_score` | float | Score services 0–10 |
| `green_spaces_score` | float | Score espaces verts 0–10 |
| `vivabilite_score` | float | Score composite 0–10 |
| `vivabilite_rank` | int | Rang Paris (1 = meilleure zone) |

---

## API

Le score est exposé via l'API FastAPI sous le préfixe `/indicators/vivabilite-familiale`.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/indicators/vivabilite-familiale` | Liste paginée, triée par rang, filtrable |
| GET | `/indicators/vivabilite-familiale/{code_iris}` | Score pour une zone IRIS spécifique |
| GET | `/indicators/vivabilite-familiale/arrondissements` | Agrégat par arrondissement |
| GET | `/indicators/vivabilite-familiale/arrondissements/{name}` | Un arrondissement |

**Paramètres de filtre (liste paginée)** :
- `arrondissement` — correspondance partielle insensible à la casse
- `min_score` / `max_score` — filtre sur `vivabilite_score` (0–10)
- `page` / `size` — pagination standard

---

## Comment lancer

```bash
# Pipeline complet (télécharge Bronze → Silver → Gold → écrit en DB)
python run_pipeline.py

# Silver seulement (nettoyage des fichiers bruts)
python run_pipeline.py --silver

# Gold seulement (recalcul des scores, requiert que Silver existe)
python run_pipeline.py --gold
```

Les 5 tables DB mises à jour par ce pipeline :

| Table DB | Script | Contenu |
|----------|--------|---------|
| `school_density` | `gold/school_density.py` | Score écoles par IRIS |
| `transport_score` | `gold/transport_score.py` | Score transport par IRIS |
| `services_score` | `gold/services_score.py` | Score services par IRIS |
| `green_spaces_score` | `gold/green_spaces_score.py` | Score espaces verts par IRIS |
| `vivabilite_familiale` | `gold/vivabilite_familiale.py` | Score composite + rang par IRIS |

---

## Décisions de conception

### Pourquoi ces 4 piliers ?

| Pilier | Pourquoi inclus | Pourquoi pas la sécurité |
|--------|----------------|--------------------------|
| Écoles | Besoin direct des familles | — |
| Transport | Pratique quotidien (trajets école, activités) | — |
| Services | Services de santé + alimentation + services du quotidien | — |
| Espaces verts | Jeux enfants, air libre, qualité de vie | — |
| ~~Sécurité~~ | ~~25 %~~ | Données SSMSI disponibles uniquement à l'échelle arrondissement (20 zones) — insuffisant face aux autres piliers à l'échelle IRIS (~992 zones). Conservé comme couche contextuelle possible. |

### Pourquoi IRIS et pas arrondissement ?

Les coordonnées GPS des écoles, arrêts de transport, hôpitaux, BDCOM et espaces verts permettent des jointures spatiales à résolution IRIS. L'échelle IRIS (~992 zones vs 20 arrondissements) révèle des disparités intra-arrondissement invisibles autrement — objectif explicite du projet.

### Normalisation

Min-max sur l'ensemble des zones IRIS parisiennes. La zone avec le score brut le plus faible obtient 0, la meilleure obtient 10. Les autres se positionnent proportionnellement. Un sous-score manquant est remplacé par la médiane de la ville (fallback gracieux).
