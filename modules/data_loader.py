import json
import pandas as pd
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


@st.cache_data
def load_products() -> list[dict]:
    with open(DATA_DIR / "metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)


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
