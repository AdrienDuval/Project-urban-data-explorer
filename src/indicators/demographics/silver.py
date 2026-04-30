"""
Silver layer — données démographiques et socio-économiques par IRIS Paris.
Sources :
  - FILO 2021 : revenus déclarés par IRIS (INSEE)
  - IC 2022   : population et CSP par IRIS (INSEE)
"""
from __future__ import annotations

import pandas as pd
from src.config import (
    DEMO_REVENUE_BRONZE,
    DEMO_CSP_BRONZE,     
    DEMO_SILVER,           
)


# Mapping codes GSEC → labels lisibles
CSP_LABELS = {
    "C22_POP15P_STAT_GSEC11_21": "agriculteurs",
    "C22_POP15P_STAT_GSEC12_22": "artisans_commercants",
    "C22_POP15P_STAT_GSEC13_23": "cadres",
    "C22_POP15P_STAT_GSEC14_24": "professions_intermediaires",
    "C22_POP15P_STAT_GSEC15_25": "employes",
    "C22_POP15P_STAT_GSEC16_26": "ouvriers",
    "C22_POP15P_STAT_GSEC32":    "retraites",
    "C22_POP15P_STAT_GSEC40":    "sans_activite",
}


def process_demographics_silver() -> None:
    print("[demographics] Loading revenue data...")

    # ── 1. Revenus ────────────────────────────────────────────────────────
    rev = pd.read_csv(DEMO_REVENUE_BRONZE, sep=";", dtype={"IRIS": str})
    rev["code_iris"] = rev["IRIS"].str.zfill(9)

    # Garder seulement Paris
    rev = rev[rev["code_iris"].str.startswith("75")].copy()

    # Convertir les colonnes numériques (ns/nd → NaN)
    numeric_cols = ["DEC_MED21", "DEC_Q121", "DEC_Q321", "DEC_GI21",
                    "DEC_PIMP21", "DEC_TP6021"]
    for col in numeric_cols:
        rev[col] = pd.to_numeric(
            rev[col].astype(str).str.replace(",", "."), errors="coerce"
        )

    rev = rev[["code_iris"] + numeric_cols].rename(columns={
        "DEC_MED21":   "revenu_median",
        "DEC_Q121":    "revenu_q1",
        "DEC_Q321":    "revenu_q3",
        "DEC_GI21":    "gini",
        "DEC_PIMP21":  "taux_imposition",
        "DEC_TP6021":  "taux_pauvrete",
    })
    print("[demographics]   %d zones revenus chargées", len(rev))

    # ── 2. Population + CSP ───────────────────────────────────────────────
    print("[demographics] Loading CSP data...")
    csp = pd.read_csv(
        DEMO_CSP_BRONZE, sep=";", low_memory=False,
        dtype={"IRIS": str, "COM": str, "LAB_IRIS": str},
    )
    csp["code_iris"] = csp["IRIS"].str.zfill(9)
    csp = csp[csp["code_iris"].str.startswith("75")].copy()

    # Colonnes population par tranche d'âge
    age_cols = {
        "P22_POP":     "population",
        "P22_POP0014": "pop_0_14",
        "P22_POP1529": "pop_15_29",
        "P22_POP2064": "pop_20_64",
        "P22_POP65P":  "pop_65p",
    }
    for col in age_cols:
        csp[col] = pd.to_numeric(csp[col], errors="coerce")

    # Colonnes CSP
    for raw_col in CSP_LABELS:
        csp[raw_col] = pd.to_numeric(csp[raw_col], errors="coerce")

    csp = csp[["code_iris", "LAB_IRIS"] + list(age_cols.keys()) + list(CSP_LABELS.keys())].copy()
    csp = csp.rename(columns={**age_cols, **CSP_LABELS, "LAB_IRIS": "nom_iris"})

    # Calcul des parts CSP (% de la population 15+)
    csp["pop_15p"] = csp[list(CSP_LABELS.values())].sum(axis=1)
    for label in CSP_LABELS.values():
        csp[f"pct_{label}"] = (csp[label] / csp["pop_15p"] * 100).round(2)

    print("[demographics]   %d zones CSP chargées", len(csp))

    # ── 3. Merge revenus + CSP ────────────────────────────────────────────
    merged = csp.merge(rev, on="code_iris", how="left")
    print("[demographics]   %d zones après merge", len(merged))
    print("[demographics]   Revenus manquants: %d zones",
                merged["revenu_median"].isna().sum())

    merged.to_csv(DEMO_SILVER, index=False)
    print("[demographics] Silver saved → %s (%d rows)",
                DEMO_SILVER.name, len(merged))


if __name__ == "__main__":
    process_demographics_silver()