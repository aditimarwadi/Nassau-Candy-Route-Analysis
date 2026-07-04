"""
data_loader.py
Handles all data ingestion, cleaning, and feature engineering
for the Nassau Candy Route Efficiency dashboard.
"""

import pandas as pd
import numpy as np
import streamlit as st
from config import PRODUCT_FACTORY_MAP


def load_and_prepare_data(filepath: str) -> pd.DataFrame:
    """
    Load the Nassau Candy CSV, clean it, and engineer all required features.

    Parameters
    ----------
    filepath : str
        Path to Nassau_Candy_Distributor.csv (relative or absolute).

    Returns
    -------
    pd.DataFrame
        Fully prepared dataframe ready for dashboard consumption.
    """

    # ── 1. Load ────────────────────────────────────────────────────────────────
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        st.error(
            f"❌ Could not find **{filepath}**.\n\n"
            "Please place `Nassau_Candy_Distributor.csv` in the same folder as `app.py` "
            "and restart the app."
        )
        st.stop()

    # ── 2. Column normalisation ────────────────────────────────────────────────
    df.columns = df.columns.str.strip()

    # Rename common variants
    rename_map = {
        "Country/Region": "Country/Region",
        "State/Province": "State/Province",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # ── 3. Date parsing & validation ───────────────────────────────────────────
    # for col in ["Order Date", "Ship Date"]:
    #     df[col] = pd.to_datetime(df[col],errors="coerce")
    for col in ["Order Date", "Ship Date"]:
    # Handle Excel serial number dates (e.g. 45292)
     if df[col].dtype in ["int64", "float64"] or pd.to_numeric(df[col], errors="coerce").notna().mean() > 0.8:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        numeric_mask = df[col].notna() & (df[col] > 40000)
        df.loc[numeric_mask, col] = pd.to_datetime(
            df.loc[numeric_mask, col], unit="D", origin="1899-12-30"
        )
        df[col] = pd.to_datetime(df[col], errors="coerce")
    else:
        df[col] = pd.to_datetime(df[col], errors="coerce")

        
    # Drop rows with unparseable dates
    n_before = len(df)
    df = df.dropna(subset=["Order Date", "Ship Date"])
    n_dropped = n_before - len(df)
    if n_dropped:
        st.sidebar.warning(f"⚠️ Dropped {n_dropped:,} rows with invalid dates.")

    # ── 4. Lead-time feature ───────────────────────────────────────────────────
    df["Lead Time (Days)"] = (df["Ship Date"] - df["Order Date"]).dt.days

    # Remove negative or zero lead times (data errors)
    df = df[df["Lead Time (Days)"] > 0]

    # ── 5. Factory assignment ──────────────────────────────────────────────────
    df["Factory"] = df["Product Name"].map(PRODUCT_FACTORY_MAP)

    # Fallback: try mapping via Division if Product Name didn't match
    if df["Factory"].isna().any():
        division_factory = {
            "Chocolate": "Wicked Choccy's",   # safe default
            "Sugar": "Sugar Shack",
            "Other": "Secret Factory",
        }
        mask = df["Factory"].isna()
        df.loc[mask, "Factory"] = df.loc[mask, "Division"].map(division_factory)

    df["Factory"] = df["Factory"].fillna("Unknown Factory")

    # ── 6. Route construction ──────────────────────────────────────────────────
    # Route = Factory → Customer State
    df["Route"] = df["Factory"] + " → " + df["State/Province"].fillna("Unknown")

    # ── 7. Geographic standardisation ─────────────────────────────────────────
    df["State/Province"] = df["State/Province"].str.strip().str.upper()
    df["Region"] = df["Region"].str.strip().str.title()

    # ── 8. Numeric coercion ────────────────────────────────────────────────────
    for col in ["Sales", "Units", "Gross Profit", "Cost"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ── 9. Derived columns ─────────────────────────────────────────────────────
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["Week"] = df["Order Date"].dt.isocalendar().week.astype(int)
    df["Year"] = df["Order Date"].dt.year
    df["DayOfWeek"] = df["Order Date"].dt.day_name()
    df["Profit Margin (%)"] = np.where(
        df["Sales"] != 0,
        (df["Gross Profit"] / df["Sales"]) * 100,
        0,
    )

    return df.reset_index(drop=True)
