from __future__ import annotations

import json
import pandas as pd
import streamlit as st
from pathlib import Path

from .product_recommender import (
    audience_label,
    gender_label,
    merge_product_tags,
    OCCASION_DISPLAY,
    STYLE_DISPLAY,
    stone_label,
)

DATA_DIR = Path(__file__).parent.parent / "data"


@st.cache_data
def load_products() -> list[dict]:
    """Load the production catalog and flatten recommendation tags onto each
    product (product_type_label, material_label, stone labels, style/occasion
    tags in Vietnamese) so the UI and prompt builder don't need to re-derive
    them on every render."""
    with open(DATA_DIR / "catalog_production_enriched.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    products = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        merged = merge_product_tags(item)
        tags = merged.get("recommendation_tags", {})
        merged["product_type_label"] = tags.get("product_type_label", "")
        merged["material_label"] = tags.get("material_label", "")
        merged["primary_stone_label"] = stone_label(tags.get("primary_stone"))
        merged["secondary_stone_label"] = stone_label(tags.get("secondary_stone"))
        merged["gender_label"] = gender_label(tags.get("gender"))
        merged["audience_label"] = audience_label(tags.get("audience"))
        # Only keep tags with a clean Vietnamese translation — raw English
        # slugs without a mapping (e.g. "accent_stone") add noise, not signal.
        merged["style_tags_vi"] = [STYLE_DISPLAY[t] for t in tags.get("style_tags", []) if t in STYLE_DISPLAY]
        merged["occasion_tags_vi"] = [OCCASION_DISPLAY[t] for t in tags.get("occasion_tags", []) if t in OCCASION_DISPLAY]
        products.append(merged)
    return products


@st.cache_data
def load_customers() -> pd.DataFrame:
    path = DATA_DIR / "customer_data_poc_enhanced.xlsx"
    workbook = pd.ExcelFile(path)
    sheet_name = "profiles_enhanced" if "profiles_enhanced" in workbook.sheet_names else workbook.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet_name)
    return df


def get_customer(df: pd.DataFrame, customer_id: str) -> dict | None:
    row = df[df["customer_id"] == customer_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def format_price(price: int | float) -> str:
    try:
        return f"{int(price):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(price)
