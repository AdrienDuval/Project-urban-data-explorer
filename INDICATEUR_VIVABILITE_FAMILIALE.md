# Indice de Vivabilite Familiale - Documentation Complete

Ce document couvre tout le parcours de l'indice de vivabilite familiale: fichiers sources, transformations Bronze/Silver/Gold, fonctions utilisees, normalisations, tables SQL, colonnes, et exposition API.

## 1) Vue d'ensemble du parcours

Pipeline d'execution (script principal): `run_pipeline.py`

- Bronze: telechargement des donnees brutes via `src/data_loader.py::load_data()`
- Silver: nettoyage/normalisation des jeux de donnees
- Gold: calcul des sous-scores et du score composite
- DB: ecriture via `to_sql(..., if_exists="replace")`
- API: lecture depuis les tables SQL via FastAPI

## 2) Localisation code (fichiers principaux)

### Orchestration
- `run_pipeline.py`
- `src/config.py`
- `src/db.py`

### Bronze -> Silver (indice vivabilite familiale)
- `src/silver/schools.py`
- `src/silver/transport.py`
- `src/silver/hospitals.py`
- `src/silver/bdcom.py`
- `src/silver/green_spaces.py`
- `src/silver/iris.py`
- `src/silver/population.py`

### Silver -> Gold (scores)
- `src/gold/school_density.py`
- `src/gold/transport_score.py`
- `src/gold/services_score.py`
- `src/gold/green_spaces_score.py`
- `src/gold/family_support_scores.py`
- `src/gold/vivabilite_familiale.py`

### API (lecture DB)
- `api/db_models.py`
- `api/services/indicators/vivabilite_service.py`
- `api/routers/indicators/vivabilite.py`
- `api/models/indicators/vivabilite.py`

## 3) Sources Bronze et sorties Silver

### A. Ecoles
- Bronze:
  - `data/bronze/indice_vivabilite_familiale/etablissements-scolaires-colleges.xlsx`
  - `data/bronze/indice_vivabilite_familiale/etablissements-scolaires-ecoles-elementaires.xlsx`
  - `data/bronze/indice_vivabilite_familiale/etablissements-scolaires-maternelles.xlsx`
- Silver output: `data/silver/schools_merged.csv`
- Fonction: `src/silver/schools.py::process_schools()`
- Fonctions internes:
  - `_load(path)` (normalisation noms de colonnes)
  - filtre types (`SCHOOL_TYPES` depuis `src/config.py`)
  - dedoublonnage (nom + adresse, annee la plus recente)
  - extraction `lat/lng` depuis `geo_point`

### B. Transport
- Bronze:
  - `data/bronze/transport_data/arrets.csv`
  - `data/bronze/transport_data/velib.csv`
- Silver outputs:
  - `data/silver/transport_arrets_paris.csv`
  - `data/silver/velib_paris.csv`
- Fonctions:
  - `src/silver/transport.py::process_transport_arrets()`
  - `src/silver/transport.py::process_velib()`
  - `src/silver/transport.py::process_transport()`
- Regles:
  - extraction coordonnees via `_split_geopoint()`
  - normalisation type (`lower()`)
  - filtre Paris (`postal_region` commencant par `75` pour arrets, `code_insee` commencant par `75` pour velib)

### C. Services et sante
- Bronze:
  - `data/bronze/public_service_data/les_etablissements_hospitaliers_franciliens.csv`
  - `data/bronze/public_service_data/BDCOM_2023.csv`
  - `data/bronze/public_service_data/BDCOM_2023_OD.xlsx`
- Silver outputs:
  - `data/silver/hospitals_paris_clean.csv`
  - `data/silver/bdcom_paris_clean.csv`
- Fonctions:
  - `src/silver/hospitals.py::process_hospitals()`
  - `src/silver/bdcom.py::process_bdcom()`

### D. Espaces verts
- Bronze:
  - `data/bronze/indice_vivabilite_familiale/espaces_verts.geojson`
- Silver output:
  - `data/silver/espaces_verts_paris.geojson`
- Fonction:
  - `src/silver/green_spaces.py::process_green_spaces()`
- Regles:
  - filtre ouvert/ferme via `_filter_open_spaces()`
  - exclusion types decoratifs (`DECORATIVE_TYPES`)
  - recalcul de `surface_totale_reelle` en EPSG:2154 si manquante

### E. Referentiels IRIS/population
- Bronze:
  - `data/bronze/main_data/iris.xlsx`
  - `data/bronze/main_data/iris.geojson`
  - `data/bronze/main_data/base-ic-evol-struct-pop-2022.CSV`
- Silver outputs:
  - `data/silver/iris_paris.csv`
  - `data/silver/population_paris.csv`
- Fonctions:
  - `src/silver/iris.py::process_iris()`
  - `src/silver/population.py::process_population()`

## 4) Calcul Gold: sous-scores et composite

## 4.1 School score
- Fichier: `src/gold/school_density.py`
- Fonction: `compute_school_density()`
- Sortie CSV: `data/gold/schools_score_iris.csv`
- Table SQL: `school_density`
- Logique:
  - points ecoles en EPSG:4326 -> EPSG:2154
  - buffer IRIS de `BUFFER_METERS` (500 m)
  - jointure spatiale `sjoin(..., predicate="within")`
  - `school_count` puis `schools_per_1000 = school_count / population * 1000`
  - normalisation `_normalize_0_10()`

## 4.2 Transport score (vivabilite)
- Fichier: `src/gold/transport_score.py`
- Fonction: `compute_transport_score()`
- Sortie CSV: `data/gold/transport_score_iris.csv`
- Table SQL: `transport_score`
- Poids types (`src/config.py::TRANSPORT_WEIGHTS`):
  - metro: 1.0
  - rail: 1.2
  - tram: 0.7
  - bus: 0.4
  - cableway: 0.5
  - velib: 0.3
- Logique:
  - concat arrets + velib
  - `weight = map(type)`
  - buffer IRIS 500 m
  - aggregation `stop_count`, `weighted_stops`
  - normalisation `_normalize_0_10(weighted_stops)`

## 4.3 Services score (legacy broad services)
- Fichier: `src/gold/services_score.py`
- Fonction: `compute_services_score()`
- Sortie CSV: `data/gold/services_score_iris.csv`
- Table SQL: `services_score`
- Parametres:
  - categories BDCOM `niv8 in {2,4}`
  - `HOSPITAL_WEIGHT = 3.0`
  - `BDCOM_WEIGHT = 1.0`
- Logique:
  - hopitaux (WGS84 -> EPSG:2154) + BDCOM (deja EPSG:2154)
  - buffer IRIS 500 m
  - `weighted_services = 3*hospital_count + 1*service_count`
  - normalisation `_normalize_0_10(weighted_services)`

## 4.4 Green spaces score
- Fichier: `src/gold/green_spaces_score.py`
- Fonction: `compute_green_spaces_score()`
- Sortie CSV: `data/gold/green_spaces_score_iris.csv`
- Table SQL: `green_spaces_score`
- Parametres:
  - `GREEN_SPACES_BUFFER_METERS = 300`
  - `ADJACENT_BONUS = 0.5`
- Logique:
  - centroides des polygones espaces verts
  - `interior_m2` (centroide dans IRIS)
  - `adjacent_m2` (centroide dans buffer 300 m mais hors interieur)
  - `total_green_m2 = interior_m2 + 0.5 * adjacent_m2`
  - `green_m2_per_resident = total_green_m2 / population`
  - normalisation `_normalize_0_10(green_m2_per_resident)`

## 4.5 Family support sub-scores (nouvelle architecture)
- Fichier: `src/gold/family_support_scores.py`
- Fonction master: `compute_family_support_scores()`
- Sous-fonctions:
  - `compute_healthcare_score()` -> CSV `data/gold/healthcare_score_iris.csv`, table `healthcare_score`
  - `compute_daily_services_score()` -> CSV `data/gold/daily_services_score_iris.csv`, table `daily_services_score`
  - `compute_neutral_family_factors()` -> CSV `data/gold/family_missing_factors_iris.csv`, table `family_missing_factors`
- Parametres:
  - `HEALTHCARE_BDCOM_WEIGHT = 1.5`
  - `HOSPITAL_WEIGHT = 3.0`
  - `DAILY_SERVICE_WEIGHT = 1.0`
  - `NEUTRAL_PLACEHOLDER_SCORE = 5.0` pour `childcare_score`, `safety_score`, `environment_score`

## 4.6 Composite vivabilite familiale (version actuelle)
- Fichier: `src/gold/vivabilite_familiale.py`
- Fonction: `compute_vivabilite_familiale()`
- Sortie CSV: `data/gold/vivabilite_familiale_iris.csv`
- Table SQL: `vivabilite_familiale`
- Inputs fusionnes:
  - `schools_score_iris.csv`
  - `transport_score_iris.csv`
  - `services_score_iris.csv`
  - `green_spaces_score_iris.csv`
  - `healthcare_score_iris.csv`
  - `daily_services_score_iris.csv`
  - `family_missing_factors_iris.csv`
- Regles:
  - fallback valeurs manquantes: mediane de la colonne score
  - `essential_connectivity_score` (transport + healthcare + daily services, 1/3 chacun)
  - `vivabilite_score` par somme ponderee
  - rangs: `vivabilite_rank`, `essential_connectivity_rank` (1 = meilleur)

## 5) Normalisations utilisees

### A. Min-max 0-10 (la plus utilisee)
Fonction typique:

```
if max == min:
    score = 5.0
else:
    score = ((x - min) / (max - min) * 10).round(2)
```

Utilisee dans:
- `src/gold/school_density.py::_normalize_0_10`
- `src/gold/transport_score.py::_normalize_0_10`
- `src/gold/services_score.py::_normalize_0_10`
- `src/gold/green_spaces_score.py::_normalize_0_10`
- `src/gold/family_support_scores.py::_normalize_0_10`

### B. Min-max 0-1 (transport API uniquement)
- `src/gold/transport_score.py::min_max_normalize`
- Utilisee pour le dataset API `transport_indicator_iris.csv` (pas le composite vivabilite)

### C. Remplissage des manquants dans le composite
- `src/gold/vivabilite_familiale.py`
- Pour chaque score composant, `NaN -> mediane de la ville`

## 6) Poids officiels (implementation actuelle)

Source: `src/config.py`

### VIVABILITE_WEIGHTS
- `school_score`: 0.20
- `childcare_score`: 0.15
- `safety_score`: 0.20
- `healthcare_score`: 0.15
- `environment_score`: 0.15
- `green_spaces_score`: 0.075
- `transport_score`: 0.05
- `daily_services_score`: 0.025

### ESSENTIAL_CONNECTIVITY_WEIGHTS
- `transport_score`: 1/3
- `healthcare_score`: 1/3
- `daily_services_score`: 1/3

## 7) Colonnes SQL: table finale `vivabilite_familiale`

Definition referencee dans `api/db_models.py::vivabilite_familiale`.

- Meta:
  - `IRIS`, `LIBCOM`, `LIBIRIS`, `GRD_QUART`, `population`, `code_iris`
- Ecoles:
  - `school_count`, `schools_per_1000`, `school_score`
- Transport:
  - `stop_count`, `weighted_stops`, `transport_score`
- Services legacy:
  - `hospital_count`, `service_count`, `weighted_services`, `services_score`
- Espaces verts:
  - `interior_m2`, `adjacent_m2`, `total_green_m2`, `green_m2_per_resident`, `green_spaces_score`
- Healthcare:
  - `healthcare_hospital_count`, `weighted_hospital_count`, `healthcare_service_count`, `weighted_healthcare_service_count`, `weighted_healthcare_access`, `healthcare_score`
- Daily services:
  - `daily_service_count`, `weighted_daily_service_count`, `daily_services_score`
- Facteurs neutres:
  - `childcare_score`, `safety_score`, `environment_score`
- Composites:
  - `essential_connectivity_score`, `essential_connectivity_weights`
  - `vivabilite_score`, `vivabilite_model`, `vivabilite_weights`, `vivabilite_rank`, `essential_connectivity_rank`

## 8) API: exposition de l'indicateur

Routeur: `api/routers/indicators/vivabilite.py`  
Service: `api/services/indicators/vivabilite_service.py`

Endpoints:
- `GET /indicators/vivabilite-familiale`
  - pagination + filtres `arrondissement`, `min_score`, `max_score`
- `GET /indicators/vivabilite-familiale/{code_iris}`
- `GET /indicators/vivabilite-familiale/arrondissements`
- `GET /indicators/vivabilite-familiale/arrondissements/{arrondissement}`

Modele de reponse:
- `api/models/indicators/vivabilite.py::VivabiliteIndicator`
- `api/models/indicators/vivabilite.py::VivabiliteArrondissementStats`

## 8.1) Comment l'API est rendue dans le front (rendering)

### A. Point d'entree front
- Client API front: `web/src/lib/api.ts`
- Page principale (landing): `web/src/app/page.tsx`
- Rendu map principal: `web/src/components/EnhancedMapDashboard.tsx`
- Version map simple (legacy/demo): `web/src/components/MapDashboard.tsx`

### B. Chaine de rendu (backend -> frontend -> UI)

1. Backend expose les endpoints FastAPI (ex: `/map/vivabilite-familiale`, `/indicators/vivabilite-familiale`, etc.)
2. `web/src/lib/api.ts` appelle ces endpoints avec `fetch(...)`
3. `EnhancedMapDashboard.tsx` charge les donnees via `useEffect` + fonctions `fetch...`
4. Les donnees GeoJSON sont injectees dans Mapbox via:
   - `<Source data={...} type="geojson">`
   - `<Layer ...>` pour coloration/contours
5. Les interactions utilisateur (hover/click/sidebar) lisent `feature.properties` pour afficher:
   - popup map
   - panneau details
   - classement ("Top matches")
   - filtres dynamiques (score mini, arrondissement, recherche)

### C. Endpoints effectivement rendus et emplacement UI

- `GET /map/vivabilite-familiale`
  - Appel: `fetchVivabiliteMap()` dans `web/src/lib/api.ts`
  - Rendu: couche carte principale dans `EnhancedMapDashboard.tsx`
  - Utilisation UI:
    - coloration des polygones (score actif)
    - popup zone (nom, score, rank)
    - panneau details droite
    - classement sidebar

- `GET /map/vivabilite-familiale/arrondissement`
  - Appel: `fetchVivabiliteArrondissement()`
  - Rendu: couche de fallback quand zoom faible (`currentZoom < ZOOM_BREAK`)
  - Utilisation UI:
    - agrandit la lecture macro de Paris avant zoom IRIS

- `GET /indicators/transport/points`
  - Appel: `fetchTransportPoints()`
  - Rendu: source GeoJSON transport + layers clusters/points/labels
  - Utilisation UI:
    - markers Metro/RER/Tram/Bus/Velib
    - popup station au clic
    - filtres par type dans la sidebar

- `GET /map/thermal-comfort`
  - Appel: `fetchThermalComfortMap()`
  - Rendu: meme composant map, metrique thermique active
  - Utilisation UI:
    - bascule indicateur principal "Confort thermique"

- `GET /map/housing/rent`
  - Appel: `fetchRentMap()`
  - Rendu: couche logement (metrique loyer)
  - Utilisation UI:
    - score d'abordabilite locative
    - enrichissement panneau details (loyer median)

- `GET /map/housing/sale`
  - Appel: `fetchSaleMap()`
  - Rendu: couche logement (metrique achat)
  - Utilisation UI:
    - score d'abordabilite achat
    - enrichissement panneau details (prix median m2)

- `GET /map/demographics`
  - Appel: `fetchDemographicsMap()`
  - Rendu: couche demographie
  - Utilisation UI:
    - revenus, gini, CSP selon metriques selectionnees

- `GET /bdcom/by-iris/{codeIris}`
  - Appel: `fetchBdcomByIris(codeIris)`
  - Rendu: panneau details zone selectionnee
  - Utilisation UI:
    - nombre d'etablissements, activites top, surface moyenne

- `GET /dvf/by-iris/{codeIris}`
  - Appel: `fetchDvfByIris(codeIris)`
  - Rendu: panneau details zone selectionnee
  - Utilisation UI:
    - nb transactions, median prix/m2, median surface

### D. Details techniques de rendu

- Le rendu cartographique se fait avec `react-map-gl/mapbox`.
- Les polygones sont rendus via:
  - `Source id="vivabilite-source"` + `Layer fill/outline/active`.
- Les points transport sont rendus via:
  - `Source id="transport-source"` + layers cluster/circle/symbol.
- Les proprietes map (`feature.properties`) sont enrichies localement:
  - `buildComputedGeojson(...)` calcule score actif/rank/percentile pour l'UI.
- Les filtres sont appliques cote front:
  - `filterComputedGeojson(...)` pour recherche, arrondissement, score minimum.

## 9) Ecriture en base de donnees

Connexion DB: `src/db.py`

- moteur SQLAlchemy cree depuis `.env`:
  - `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- chaque etape Gold persiste en SQL via:
  - `DataFrame.to_sql("<table_name>", engine, if_exists="replace", index=False)`

## 10) Commandes d'execution

```bash
# complet: Bronze -> Silver -> Gold
python run_pipeline.py

# uniquement Silver
python run_pipeline.py --silver

# uniquement Gold (Silver deja present)
python run_pipeline.py --gold
```

## 11) Notes importantes de coherence

- La documentation ancienne "4 piliers a 25%" n'est plus la formule active dans le code.
- Le code actif utilise un composite elargi (`VIVABILITE_WEIGHTS`) avec des facteurs neutres (5.0) tant que certaines donnees IRIS ne sont pas disponibles.
- Le champ `services_score` est encore conserve dans la table finale, mais le composite principal actuel s'appuie surtout sur `healthcare_score` et `daily_services_score` pour la composante services du quotidien.
