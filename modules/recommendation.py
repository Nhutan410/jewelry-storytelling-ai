"""Bridges Storytelling's customer schema (Vietnamese POC columns) to the
ProductRecommender ported from jewelry_nba, without touching its scoring logic.

jewelry_nba's own customer sheet has `gender`, `age`, `lep_intent` columns.
Storytelling's `customer_data_poc_enhanced.xlsx` has `gioi_tinh`, `tuoi`, and a
Vietnamese `persona` string instead — this module only translates field names
and persona text into the vocabulary `ProductRecommender` already understands
(engagement/anniversary/gift/self_reward), then delegates all filtering and
scoring to the untouched recommender.
"""
from __future__ import annotations

import streamlit as st

from .product_recommender import ProductRecommender, normalize_text

# Persona/cluster phrases (Vietnamese, accent-stripped by normalize_text) mapped
# to the lep_intent-style tokens ProductRecommender._profile_preferences reads.
_PERSONA_INTENT_MAP = [
    (("cau hon", "dinh hon", "engagement"), "engagement"),
    (("ky niem", "anniversary"), "anniversary"),
    (("qua tang", "gift buyer", "gift"), "gift"),
    (("tu thuong", "self reward", "self-reward", "self"), "self_reward"),
]


def _infer_lep_intent(customer: dict) -> str:
    text = normalize_text(" ".join(str(customer.get(k, "")) for k in ("persona", "cluster", "persona_ml", "cluster_ml")))
    tokens = [token for keywords, token in _PERSONA_INTENT_MAP if any(k in text for k in keywords)]
    seen = []
    for token in tokens:
        if token not in seen:
            seen.append(token)
    return " ".join(seen)


def build_recommendation_profile(customer: dict) -> dict:
    """Translate a Storytelling customer row into the profile shape ProductRecommender expects."""
    profile = dict(customer)
    profile["gender"] = customer.get("gioi_tinh", "")
    profile["age"] = customer.get("tuoi", "")
    profile["lep_intent"] = _infer_lep_intent(customer)
    return profile


@st.cache_resource(show_spinner=False)
def get_recommender() -> ProductRecommender:
    """Load the production catalog once per Streamlit session."""
    return ProductRecommender()


def get_recommendations_for_customer(customer: dict, top_n: int | None = 200) -> list[dict]:
    """Return scored product recommendations for one customer, sorted best-first."""
    if not customer:
        return []
    recommender = get_recommender()
    profile = build_recommendation_profile(customer)
    return recommender.recommend_for_profile(profile, top_n=top_n)
