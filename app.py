import os
import math
import hmac
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from modules.data_loader import load_products, load_customers, get_customer, format_price
from modules.framework_selector import (
    select_framework, extract_signals, get_persona_icon,
    get_selection_explanation, FRAMEWORKS, DECISION_RULES,
)
from modules.prompt_builder import build_custom_story_inputs, select_custom_story_framework
from modules.story_generator import generate_story_stream, generate_zalo_stream, generate_custom_story_stream
from modules.product_recommender import PRODUCT_TYPE_LABELS, SCORE_WEIGHTS, canonical_product_type
from modules.recommendation import get_recommendations_for_customer

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PNJ AI Storytelling",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --gold:        #B8860B;
    --gold-light:  #D4AF37;
    --gold-pale:   #FDF6E3;
    --dark:        #1A1A1A;
    --text:        #2D2D2D;
    --muted:       #6B6B6B;
    --border:      #E8DCC8;
    --bg:          #FAF7F2;
    --hero:        #8B4513;
    --golden:      #B8860B;
    --emotional:   #C2185B;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: 'Inter', sans-serif;
    color: var(--text);
}
[data-testid="stAppViewContainer"] > .main { background-color: var(--bg); }

/* ── Header ── */
.pnj-header {
    background: var(--dark);
    border-bottom: 2px solid var(--gold);
    padding: 18px 32px;
    margin: -1rem -1rem 1.5rem -1rem;
    display: flex; align-items: center; gap: 16px;
}
.pnj-header h1 {
    font-family: 'Playfair Display', serif;
    color: var(--gold-light);
    font-size: 1.7rem; margin: 0; font-weight: 700; letter-spacing: 0.5px;
}
.pnj-header p { color: #aaa; font-size: 0.82rem; margin: 0; letter-spacing: 1px; text-transform: uppercase; }

/* ── Login ── */
.login-header {
    background: #12343B;
    border-bottom: 3px solid var(--gold-light);
    box-shadow: 0 10px 28px rgba(18,52,59,0.16);
}
.login-header h1 { color: #F8D56B; }
.login-header p { color: #F6EBD0; }
.login-note {
    background: #FFF8E8;
    border: 1px solid #E6C86D;
    border-radius: 10px;
    color: #4F3A11;
    font-size: 0.88rem;
    line-height: 1.6;
    margin-bottom: 14px;
    padding: 12px 14px;
}
[data-testid="stForm"] {
    background: #FFFFFF;
    border: 1px solid #D7C18D;
    border-radius: 14px;
    box-shadow: 0 16px 40px rgba(45,35,12,0.12);
    padding: 24px 26px 28px;
}
[data-testid="stForm"] h3 {
    color: #12343B;
    font-family: 'Playfair Display', serif;
    font-size: 1.45rem;
    margin-bottom: 0.25rem;
}
[data-testid="stForm"] label {
    color: #2D2D2D !important;
    font-weight: 600 !important;
}
[data-testid="stForm"] input {
    background: #FFFDF8 !important;
    border-color: #CDB36F !important;
    color: #1F1F1F !important;
}
[data-testid="stFormSubmitButton"] button {
    background: #12343B !important;
    border: 1px solid #12343B !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    background: var(--gold) !important;
    border-color: var(--gold) !important;
    color: #FFFFFF !important;
}

/* ── Product cards ── */
.product-card {
    background: #fff; border: 1px solid var(--border); border-radius: 12px;
    padding: 14px; transition: all 0.25s ease; height: 100%; position: relative; overflow: hidden;
}
.product-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(184,134,11,0.15);
    border-color: var(--gold-light);
}
.product-card img { width: 100%; aspect-ratio: 1/1; object-fit: cover; border-radius: 8px; background: var(--gold-pale); }
.prod-name {
    font-family: 'Playfair Display', serif; font-size: 0.88rem; font-weight: 600;
    color: var(--text); margin: 10px 0 4px;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    overflow: hidden; line-height: 1.4; min-height: 2.5rem;
}
.prod-price { color: var(--gold); font-weight: 700; font-size: 1rem; margin: 4px 0 2px; }
.prod-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 6px; }
.prod-tag {
    background: var(--gold-pale); color: var(--gold); border: 1px solid var(--border);
    border-radius: 6px; padding: 1px 7px; font-size: 0.7rem; font-weight: 600;
}

/* ── Recommendation score badge ── */
.score-ribbon {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 6px; font-size: 0.78rem;
}
.score-value { font-weight: 800; font-size: 0.95rem; }
.score-evidence { color: var(--muted); font-size: 0.74rem; line-height: 1.5; margin: 2px 0 8px; min-height: 2.1rem; }
.mode-toggle-caption { color: var(--muted); font-size: 0.82rem; margin: 2px 0 10px; }

/* ── Score breakdown (bên trong expander "Chi tiết điểm") ── */
.score-bar-row { margin: 5px 0; }
.score-bar-label { display: flex; justify-content: space-between; color: var(--muted); font-size: 0.74rem; }
.score-bar-track { height: 6px; background: var(--gold-pale); border: 1px solid var(--border); border-radius: 99px; overflow: hidden; margin-top: 3px; }
.score-bar-fill { height: 100%; background: var(--gold); border-radius: 99px; }

/* ── Catalog mode radio (Gợi ý / Toàn bộ danh mục) — force dark, bold text
   regardless of the viewer's OS/browser theme, for readability ── */
[data-testid="stRadio"] label p,
[data-testid="stRadio"] label span {
    color: var(--text) !important;
    font-weight: 700 !important;
}

/* ── Badges ── */
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; margin: 2px;
}
.badge-hero      { background:#FFF3E0; color:#8B4513; border:1px solid #FFCC80; }
.badge-golden    { background:#FFF9C4; color:#B8860B; border:1px solid #FFE57F; }
.badge-emotional { background:#FCE4EC; color:#C2185B; border:1px solid #F48FB1; }
.badge-signal    { background:#E3F2FD; color:#1565C0; border:1px solid #90CAF9; font-size:0.72rem; }
.badge-rule-type { background:#F3E5F5; color:#6A1B9A; border:1px solid #CE93D8; font-size:0.7rem; }

/* ── Customer panel ── */
.customer-panel { background:#fff; border:1px solid var(--border); border-radius:14px; padding:18px; }
.customer-avatar { font-size: 2.8rem; text-align: center; margin-bottom: 8px; }
.info-table { width:100%; border-collapse:collapse; font-size:0.82rem; margin-top:8px; }
.info-table td { padding:4px 6px; border-bottom:1px solid var(--border); }
.info-table td:first-child { color:var(--muted); font-weight:500; white-space:nowrap; }
.info-table td:last-child { color:var(--text); font-weight:600; }

/* ── Story panel ── */
.story-panel { background:#fff; border:1px solid var(--border); border-radius:14px; padding:24px; margin-top:20px; }
.story-header {
    font-family:'Playfair Display', serif; color:var(--gold); font-size:1.1rem;
    font-weight:700; border-bottom:1px solid var(--border); padding-bottom:10px; margin-bottom:16px;
}
.story-text { font-style:italic; line-height:1.9; font-size:0.95rem; color:var(--text); white-space:pre-wrap; }
.original-desc {
    background: var(--gold-pale); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px; font-size: 0.88rem; line-height: 1.7; color: var(--muted);
    font-style: italic; height: 100%;
}
.compare-label {
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; color: var(--muted); margin-bottom: 8px;
}

/* ── Metrics ── */
.metric-row { display:flex; gap:10px; margin-top:10px; }
.metric-card { flex:1; background:var(--gold-pale); border-radius:8px; padding:8px 10px; text-align:center; }
.metric-card .metric-val { font-weight:700; color:var(--gold); font-size:0.95rem; }
.metric-card .metric-lbl { color:var(--muted); font-size:0.7rem; }

/* ── Misc ── */
.pagination-info { text-align:center; color:var(--muted); font-size:0.82rem; margin:8px 0; }
.section-title { font-family:'Playfair Display', serif; font-size:1.05rem; font-weight:700; color:var(--text); margin-bottom:12px; }
.gold-divider { border:none; border-top:1px solid var(--border); margin:14px 0; }
.api-warning { background:#FFF3CD; border:1px solid #FFCA28; border-radius:8px; padding:12px 16px; color:#856404; font-size:0.88rem; margin-bottom:16px; }
.img-placeholder {
    width:100%; aspect-ratio:1/1; background:var(--gold-pale); border-radius:8px;
    display:flex; align-items:center; justify-content:center; font-size:2.5rem;
    border:1px dashed var(--border);
}

/* ── Zalo message panel ── */
.zalo-panel {
    background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
    border: 1.5px solid #66bb6a;
    border-radius: 14px;
    padding: 20px 24px;
    margin-top: 20px;
}
.zalo-header {
    display: flex; align-items: center; gap: 10px;
    font-weight: 700; font-size: 1rem; color: #2e7d32;
    border-bottom: 1px solid #a5d6a7; padding-bottom: 10px; margin-bottom: 14px;
}
.zalo-badge {
    background: #43a047; color: #fff; border-radius: 12px;
    padding: 2px 10px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px;
}
.zalo-bubble {
    background: #fff; border-radius: 0 14px 14px 14px;
    border: 1px solid #c8e6c9; padding: 14px 18px;
    font-size: 0.93rem; line-height: 1.8; color: #1a1a1a;
    box-shadow: 0 2px 8px rgba(76,175,80,0.08);
    white-space: pre-wrap; max-width: 520px;
}
.zalo-hint {
    font-size: 0.75rem; color: #66bb6a; margin-top: 10px; font-style: italic;
}

/* ── Decision rules (Tab 2) ── */
.rule-row {
    display:flex; align-items:center; gap:10px; padding:8px 12px;
    border-radius:8px; margin-bottom:6px; font-size:0.85rem;
}
.rule-triggered { background:#E8F5E9; border:1px solid #A5D6A7; }
.rule-normal    { background:#fafafa; border:1px solid #eee; color:var(--muted); }
.rule-priority  { font-weight:700; color:var(--muted); font-size:0.75rem; min-width:22px; }
.rule-condition { flex:1; }
.rule-result    { font-weight:600; font-size:0.8rem; }
.rule-check     { font-size:1rem; }

/* ── Framework guide cards (Tab 3) ── */
.fw-card { background:#fff; border:1px solid var(--border); border-radius:14px; padding:22px; margin-bottom:16px; }
.fw-card-hero     { border-left:4px solid #8B4513; }
.fw-card-golden   { border-left:4px solid #B8860B; }
.fw-card-emotional{ border-left:4px solid #C2185B; }
.fw-card-title { font-family:'Playfair Display', serif; font-size:1.2rem; font-weight:700; margin-bottom:4px; }
.fw-section-label { font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:var(--muted); margin:12px 0 4px; }
.fw-example { background:var(--gold-pale); border-left:3px solid var(--gold); padding:14px 16px; border-radius:0 8px 8px 0; font-style:italic; line-height:1.8; font-size:0.88rem; }

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background-color: #F0EAD6 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border-bottom: none !important;
}
[data-baseweb="tab"] {
    background-color: transparent !important;
    color: #6B6B6B !important;
    border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
    border: none !important;
    transition: all 0.2s ease !important;
}
[data-baseweb="tab"]:hover {
    background-color: #E8DCC8 !important;
    color: #2D2D2D !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background-color: #B8860B !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(184,134,11,0.35) !important;
}
[data-baseweb="tab-highlight"] {
    display: none !important;
}
[data-baseweb="tab-border"] {
    display: none !important;
}

/* ── Buttons ── */
.stButton > button {
    background-color: var(--gold-pale) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover:not([disabled]) {
    background-color: var(--gold) !important;
    color: #fff !important;
    border-color: var(--gold) !important;
}
.stButton > button[disabled] {
    background-color: #f0f0f0 !important;
    color: #bbb !important;
    border-color: #e5e5e5 !important;
    cursor: not-allowed !important;
}
</style>
""", unsafe_allow_html=True)

# ── Login gate ────────────────────────────────────────────────────────────────
def _get_auth_config() -> tuple[str, str]:
    username = os.getenv("AUTH_USERNAME")
    password = os.getenv("AUTH_PASSWORD")
    if not username or not password:
        st.error("Thiếu AUTH_USERNAME hoặc AUTH_PASSWORD trong file .env.")
        st.stop()
    return username, password


def _render_login() -> None:
    expected_username, expected_password = _get_auth_config()

    st.markdown("""
    <div class="pnj-header login-header">
      <div>
        <h1>💎 PNJ AI Storytelling Assistant</h1>
        <p>Đăng nhập để tiếp tục</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, login_col, _ = st.columns([1, 1, 1])
    with login_col:
        with st.form("login_form"):
            st.markdown("### Đăng nhập")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Đăng nhập", use_container_width=True)

        if submitted:
            valid_username = hmac.compare_digest(username, expected_username)
            valid_password = hmac.compare_digest(password, expected_password)
            if valid_username and valid_password:
                st.session_state.authenticated = True
                st.rerun()
            st.error("Username hoặc password không đúng.")


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    _render_login()
    st.stop()

with st.sidebar:
    if st.button("Đăng xuất", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ── Session state defaults ─────────────────────────────────────────────────────
for key, default in {
    "selected_product": None,
    "story": None,
    "zalo_msg": None,
    "story_customer_id": None,
    "story_product_id": None,
    "story_framework": None,
    "story_mode": "classic",
    "custom_story": None,
    "custom_inputs": None,
    "custom_retry_temp": 0.82,
    "page": 0,
    "retry_temp": 0.85,
    "current_customer_id": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Load data ──────────────────────────────────────────────────────────────────
products = load_products()
customers_df = load_customers()
products_by_id = {p.get("product_id"): p for p in products}

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pnj-header">
  <div>
    <h1>💎 PNJ AI Storytelling Assistant</h1>
    <p>Cá nhân hóa câu chuyện trang sức · Powered by GPT-4o</p>
  </div>
</div>
""", unsafe_allow_html=True)

# API key warning
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.markdown("""
    <div class="api-warning">
      ⚠️ <strong>OPENAI_API_KEY chưa được thiết lập.</strong>
      Tạo file <code>.env</code> với nội dung <code>OPENAI_API_KEY=sk-...</code> rồi khởi động lại app.
    </div>
    """, unsafe_allow_html=True)

# ── Helper functions ──────────────────────────────────────────────────────────
def _get_fit_reason(framework_key: str, persona: str) -> str:
    reasons = {
        "Hero's Journey": f"Khách hàng với persona <em>'{persona}'</em> đang tìm kiếm sự tự công nhận. Câu chuyện Hero's Journey chạm đúng vào cảm giác 'mình xứng đáng được điều này' mà không cần ai khác công nhận.",
        "Golden Circle": f"Khách hàng với persona <em>'{persona}'</em> đang ở khoảnh khắc trọng đại. Họ cần câu chuyện bắt đầu từ ý nghĩa sâu xa — WHY — không phải từ thông số sản phẩm.",
        "Emotional Branding": f"Khách hàng với persona <em>'{persona}'</em> đang mua cho người khác. Câu chuyện cần hướng hoàn toàn vào người nhận — phẩm chất của họ, khoảnh khắc trao quà, cảm xúc họ sẽ có.",
    }
    return reasons.get(framework_key, "")


def _format_target_personas(targets: list) -> str:
    persona_map = {
        "tự thưởng": "Người thích tự thưởng",
        "self-reward": "Self-Reward Cluster",
        "cầu hôn": "Người sắp cầu hôn",
        "kỷ niệm": "Khách mua dịp kỷ niệm",
        "engagement": "Engagement Cluster",
        "anniversary": "Anniversary Cluster",
        "quà": "Người mua quà tặng",
        "gift": "Gift Buyer Cluster",
    }
    labels = [persona_map.get(t, t) for t in targets]
    return " · ".join(labels)


def _score_color(score: float) -> str:
    if score >= 85:
        return "#2E7D32"
    if score >= 70:
        return "#B8860B"
    return "#9E9E9E"


SCORE_BREAKDOWN_LABELS = {
    "budget": "Ngân sách",
    "category": "Loại SP",
    "occasion": "Dịp mua",
    "material_stone": "Chất liệu/đá",
    "recipient_profile": "Tệp người thụ hưởng",
    "style": "Style",
    "segment_value": "Phân khúc",
    "popularity": "Bán chạy",
}


def _render_score_breakdown(breakdown: dict) -> None:
    """Render each scoring component as a labeled progress bar (0 → weight)."""
    if not isinstance(breakdown, dict) or not breakdown:
        st.caption("Không có dữ liệu chi tiết điểm.")
        return
    rows = []
    for key, label in SCORE_BREAKDOWN_LABELS.items():
        if key not in breakdown:
            continue
        max_value = SCORE_WEIGHTS.get(key, 0)
        value = float(breakdown.get(key) or 0)
        pct = 0 if max_value <= 0 else max(0, min(100, value / max_value * 100))
        rows.append(f"""
        <div class="score-bar-row">
          <div class="score-bar-label"><span>{label}</span><span>{value:g}/{max_value:g}</span></div>
          <div class="score-bar-track"><div class="score-bar-fill" style="width:{pct:.0f}%"></div></div>
        </div>
        """)
    st.markdown("".join(rows), unsafe_allow_html=True)


def _matches_gender_filter(item: dict, gender_filter: str) -> bool:
    """Works for both full-catalog products (gender_label/audience_label keys)
    and recommender score dicts (gender/audience keys already Vietnamese-labeled)."""
    if gender_filter == "Tất cả":
        return True
    if gender_filter == "Trẻ em":
        return (item.get("audience_label") or item.get("audience") or "") == "Trẻ em"
    return (item.get("gender_label") or item.get("gender") or "") == gender_filter


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_main, tab_why, tab_guide = st.tabs([
    "🛍️  Danh Mục & Câu Chuyện",
    "🧭  Tại Sao Chọn Phương Pháp Này?",
    "📚  Hướng Dẫn 3 Phương Pháp Storytelling",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Danh Mục & Câu Chuyện
# ═══════════════════════════════════════════════════════════════════════════════
with tab_main:
    col_left, col_right = st.columns([3, 7], gap="medium")

    # ── Cột trái — Customer Panel ──────────────────────────────────────────────
    with col_left:
        st.markdown('<div class="section-title">👤 Khách hàng hiện tại</div>', unsafe_allow_html=True)

        customer_ids = customers_df["customer_id"].tolist()

        def customer_label(cid):
            row = customers_df[customers_df["customer_id"] == cid]
            if row.empty:
                return cid
            return f"{cid} — {row.iloc[0].get('persona', '')}"

        selected_id = st.selectbox(
            "Chọn khách hàng",
            options=customer_ids,
            format_func=customer_label,
            label_visibility="collapsed",
        )
        # Share selection with other tabs
        st.session_state.current_customer_id = selected_id

        customer = get_customer(customers_df, selected_id)

        if customer:
            framework_key = select_framework(customer)
            fw = FRAMEWORKS[framework_key]
            signals = extract_signals(customer)
            persona = customer.get("persona", "")
            icon = get_persona_icon(persona)

            badge_class = {
                "Hero's Journey": "badge-hero",
                "Golden Circle": "badge-golden",
                "Emotional Branding": "badge-emotional",
            }.get(framework_key, "badge-hero")

            st.markdown(f"""
            <div class="customer-panel">
              <div class="customer-avatar">{icon}</div>
              <div style="text-align:center;margin-bottom:10px;">
                <div style="font-weight:700;font-size:1rem;color:#1A1A1A">{selected_id}</div>
                <span class="badge {badge_class}">{persona}</span><br/>
                <span class="badge {badge_class}" style="margin-top:6px">
                  {fw['icon']} {fw['name']} — {fw['short_desc']}
                </span>
              </div>
              <hr class="gold-divider"/>
              <table class="info-table">
                <tr><td>Giới tính</td><td>{customer.get('gioi_tinh','—')}</td></tr>
                <tr><td>Tuổi</td><td>{customer.get('tuoi','—')}</td></tr>
                <tr><td>Nghề nghiệp</td><td>{customer.get('nghe_nghiep','—')}</td></tr>
                <tr><td>Phong cách</td><td>{customer.get('style','—')}</td></tr>
                <tr><td>Ngân sách</td><td>{customer.get('budget','—')}</td></tr>
                <tr><td>Ưa thích</td><td>{customer.get('preferred_type','—')} / {customer.get('material','—')}</td></tr>
                <tr><td>Phân khúc</td><td>{customer.get('segment_rfm_tier','—')}</td></tr>
              </table>
              <hr class="gold-divider"/>
              <div style="font-size:0.78rem;font-weight:600;color:#6B6B6B;margin-bottom:6px">TÍN HIỆU HÀNH VI</div>
            """, unsafe_allow_html=True)

            if signals:
                chips = "".join(f'<span class="badge badge-signal">{s}</span>' for s in signals)
                st.markdown(chips, unsafe_allow_html=True)
            else:
                st.markdown('<span style="color:#aaa;font-size:0.8rem;font-style:italic">Chưa có tín hiệu đặc biệt</span>', unsafe_allow_html=True)

            monetary = customer.get("monetary", 0)
            frequency = customer.get("frequency", 0)
            recency = customer.get("recency_days", customer.get("recency", "—"))

            try:
                monetary_fmt = f"{float(monetary)/1_000_000:.1f}M VND"
            except (ValueError, TypeError):
                monetary_fmt = "—"
            try:
                freq_fmt = f"{int(float(frequency))} lần"
            except (ValueError, TypeError):
                freq_fmt = "—"
            try:
                recency_fmt = f"{int(float(recency))} ngày trước"
            except (ValueError, TypeError):
                recency_fmt = str(recency)

            st.markdown(f"""
              <hr class="gold-divider"/>
              <div class="metric-row">
                <div class="metric-card">
                  <div class="metric-val">{monetary_fmt}</div>
                  <div class="metric-lbl">Tổng chi tiêu</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{freq_fmt}</div>
                  <div class="metric-lbl">Lần mua</div>
                </div>
              </div>
              <div style="text-align:center;font-size:0.75rem;color:#aaa;margin-top:8px">
                Lần cuối: {recency_fmt}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Cột phải — Product Catalog ─────────────────────────────────────────────
    with col_right:
        st.markdown('<div class="section-title">🛍️ Danh mục sản phẩm</div>', unsafe_allow_html=True)

        # Reset trang khi đổi khách hàng, để không bị lệch trang giữa 2 tệp dữ liệu khác nhau
        if st.session_state.get("catalog_customer_id") != selected_id:
            st.session_state.catalog_customer_id = selected_id
            st.session_state.page = 0

        catalog_mode = st.radio(
            "Chế độ hiển thị",
            options=["reco", "all"],
            format_func=lambda v: "🎯 Sản phẩm gợi ý cho khách" if v == "reco" else "📋 Toàn bộ danh mục",
            horizontal=True,
            label_visibility="collapsed",
            key="catalog_mode",
        )

        recommendations: list[dict] = []
        if catalog_mode == "reco" and customer:
            recommendations = get_recommendations_for_customer(customer, top_n=200)

        if catalog_mode == "reco":
            if recommendations:
                filtered_count = recommendations[0].get("filtered_count", len(recommendations))
                st.markdown(
                    f'<div class="mode-toggle-caption">🎯 {len(recommendations)} sản phẩm phù hợp nhất '
                    f'(trên {filtered_count} sản phẩm đã qua bộ lọc cứng theo ngân sách/loại SP/người thụ hưởng), '
                    f'xếp hạng theo điểm phù hợp — cùng logic gợi ý như hệ thống NBA.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="mode-toggle-caption">🎯 Chưa tìm được sản phẩm khớp cứng cho khách này — hãy thử xem "Toàn bộ danh mục".</div>',
                    unsafe_allow_html=True,
                )
            source_products = recommendations
        else:
            source_products = products

        f1, f2, f3, f4 = st.columns([3, 2, 2, 2])
        with f1:
            search_q = st.text_input("Tìm kiếm", placeholder="Tìm theo tên...", label_visibility="collapsed")
        with f2:
            gender_filter = st.selectbox("Giới tính", ["Tất cả", "Nữ", "Nam", "Unisex", "Trẻ em"], label_visibility="collapsed")

        cat_opts = ["Tất cả"] + list(dict.fromkeys(PRODUCT_TYPE_LABELS.values()))

        with f3:
            cat_filter = st.selectbox("Loại SP", cat_opts, label_visibility="collapsed")
        with f4:
            if catalog_mode == "all":
                smart_filter = st.button("⚡ Lọc theo KH", use_container_width=True)
            else:
                smart_filter = False
                st.markdown(
                    '<div style="padding-top:8px;color:var(--muted);font-size:0.78rem">Đã cá nhân hoá theo khách</div>',
                    unsafe_allow_html=True,
                )

        all_prices = [p.get("price", 0) for p in products if p.get("price", 0) > 0]
        min_price, max_price = int(min(all_prices)), int(max(all_prices))
        price_range = st.slider(
            "Giá (VND)", min_value=min_price, max_value=max_price,
            value=(min_price, max_price), step=500_000, format="%d",
            label_visibility="collapsed",
        )

        if smart_filter and customer:
            desired_type = canonical_product_type(customer.get("preferred_type", ""))
            if desired_type:
                cat_filter = PRODUCT_TYPE_LABELS.get(desired_type, cat_filter)

        # Filter — áp dụng cùng bộ lọc cho cả 2 chế độ, giữ nguyên thứ tự gốc
        # (theo điểm phù hợp ở chế độ gợi ý, theo catalog ở chế độ toàn bộ)
        filtered = [
            p for p in source_products
            if (not search_q or search_q.lower() in p.get("name", "").lower())
            and _matches_gender_filter(p, gender_filter)
            and (cat_filter == "Tất cả" or p.get("product_type_label", "") == cat_filter)
            and price_range[0] <= p.get("price", 0) <= price_range[1]
        ]

        PAGE_SIZE = 12
        total_pages = max(1, math.ceil(len(filtered) / PAGE_SIZE))
        if st.session_state.page >= total_pages:
            st.session_state.page = 0

        start = st.session_state.page * PAGE_SIZE
        page_products = filtered[start: start + PAGE_SIZE]

        st.markdown(
            f'<div class="pagination-info">Hiển thị {start+1}–{min(start+PAGE_SIZE, len(filtered))} / {len(filtered)} sản phẩm</div>',
            unsafe_allow_html=True,
        )

        if not page_products:
            st.info("Không tìm thấy sản phẩm phù hợp.")
        else:
            grid = st.columns(3, gap="small")
            for idx, prod in enumerate(page_products):
                with grid[idx % 3]:
                    pid = prod.get("product_id")
                    name = prod.get("name", "Sản phẩm")
                    price = prod.get("price", 0)
                    image_url = prod.get("image_url", "")
                    product_type_label = prod.get("product_type_label", "")
                    material_label = prod.get("material_label") or prod.get("material", "")
                    stone_label = prod.get("primary_stone_label") or prod.get("primary_stone", "")

                    if image_url:
                        img_html = f'<img src="{image_url}" alt="{name}" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'" /><div class="img-placeholder" style="display:none">💍</div>'
                    else:
                        img_html = '<div class="img-placeholder">💍</div>'

                    stone_chip = stone_label if stone_label and stone_label != "Không gắn đá" else ""
                    tag_chips = "".join(
                        f'<span class="prod-tag">{t}</span>'
                        for t in [product_type_label, material_label, stone_chip] if t
                    )

                    score_html = ""
                    if catalog_mode == "reco":
                        score = float(prod.get("score") or 0)
                        color = _score_color(score)
                        top_reason = (prod.get("evidence") or ["—"])[0]
                        score_html = (
                            '<div class="score-ribbon">'
                            f'<span class="prod-tag">#{idx + 1 + start}</span>'
                            f'<span class="score-value" style="color:{color}">{score:.0f}/100</span>'
                            '</div>'
                            f'<div class="score-evidence">{top_reason}</div>'
                        )

                    st.markdown(f"""
                    <div class="product-card">
                      {img_html}
                      {score_html}
                      <div class="prod-name">{name}</div>
                      <div class="prod-price">{format_price(price)} ₫</div>
                      <div class="prod-tags">{tag_chips}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if catalog_mode == "reco":
                        with st.expander("📊 Chi tiết điểm", expanded=False):
                            _render_score_breakdown(prod.get("score_breakdown") or {})

                    btn_old, btn_new = st.columns(2)
                    with btn_old:
                        if st.button("📖 Kể chuyện", key=f"btn_{pid}_{idx}", use_container_width=True):
                            st.session_state.selected_product = products_by_id.get(pid, prod)
                            st.session_state.story_mode = "classic"
                            st.session_state.story = None
                            st.session_state.zalo_msg = None
                            st.session_state.custom_story = None
                            st.session_state.custom_inputs = None
                            st.session_state.story_customer_id = selected_id
                            st.session_state.story_product_id = pid
                            st.session_state.story_framework = framework_key
                            st.session_state.retry_temp = 0.85
                            st.rerun()
                    with btn_new:
                        if st.button("✨ Bộ content", key=f"custom_btn_{pid}_{idx}", use_container_width=True):
                            full_prod = products_by_id.get(pid, prod)
                            st.session_state.selected_product = full_prod
                            st.session_state.story_mode = "custom"
                            st.session_state.story = None
                            st.session_state.zalo_msg = None
                            st.session_state.custom_story = None
                            st.session_state.custom_inputs = build_custom_story_inputs(customer, full_prod)
                            st.session_state.story_customer_id = selected_id
                            st.session_state.story_product_id = pid
                            st.session_state.story_framework = framework_key
                            st.session_state.custom_retry_temp = 0.82
                            st.rerun()

        # Pagination
        pg1, pg2, pg3 = st.columns([2, 3, 2])
        with pg1:
            if st.button("◀ Trước", disabled=st.session_state.page == 0, use_container_width=True):
                st.session_state.page -= 1
                st.rerun()
        with pg2:
            st.markdown(
                f'<div class="pagination-info">Trang {st.session_state.page + 1} / {total_pages}</div>',
                unsafe_allow_html=True,
            )
        with pg3:
            if st.button("Tiếp ▶", disabled=st.session_state.page >= total_pages - 1, use_container_width=True):
                st.session_state.page += 1
                st.rerun()

    # ── Story Panel ────────────────────────────────────────────────────────────
    prod = st.session_state.selected_product
    if prod:
        fw_key = st.session_state.story_framework or framework_key
        fw = FRAMEWORKS[fw_key]
        story_mode = st.session_state.get("story_mode", "classic")
        if story_mode == "custom" and st.session_state.custom_inputs is None:
            cust_data = get_customer(customers_df, st.session_state.story_customer_id)
            st.session_state.custom_inputs = build_custom_story_inputs(cust_data, prod)
        custom_framework = None
        if story_mode == "custom" and st.session_state.custom_inputs:
            custom_framework, _ = select_custom_story_framework(st.session_state.custom_inputs)

        st.markdown("---")
        if story_mode == "custom":
            st.markdown(f"""
            <div class="story-panel">
              <div class="story-header">
                ✨ BỘ NỘI DUNG STORYTELLING &nbsp;·&nbsp;
                {custom_framework or 'Framework theo prompt mới'} &nbsp;·&nbsp;
                cho {st.session_state.story_customer_id} &nbsp;·&nbsp;
                <span style="color:#888;font-size:0.88rem">{prod.get('name','')[:55]}…</span>
              </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="story-panel">
              <div class="story-header">
                📖 CÂU CHUYỆN CÁ NHÂN HÓA &nbsp;·&nbsp;
                {fw['icon']} {fw['name']} &nbsp;·&nbsp;
                cho {st.session_state.story_customer_id} &nbsp;·&nbsp;
                <span style="color:#888;font-size:0.88rem">{prod.get('name','')[:55]}…</span>
              </div>
            """, unsafe_allow_html=True)

        # Mini product info
        sp1, sp2 = st.columns([1, 4])
        with sp1:
            img_url = prod.get("image_url", "")
            if img_url:
                st.markdown(
                    f'<img src="{img_url}" style="width:100%;border-radius:8px;aspect-ratio:1/1;object-fit:cover" onerror="this.style.display:none"/>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div style="font-size:3rem;text-align:center">💍</div>', unsafe_allow_html=True)
        with sp2:
            st.markdown(f"""
            **{prod.get('name','')}**
            - Giá: **{format_price(prod.get('price',0))} ₫**
            - Chất liệu: {prod.get('material_label','') or '—'}
            - Đá chính: {prod.get('primary_stone_label','') or '—'}
            - Loại SP: {prod.get('product_type_label','') or '—'}
            - Mã SKU: `{prod.get('sku','')}`
            """)

        st.markdown("---")

        if story_mode == "custom":
            custom_inputs = st.session_state.custom_inputs
            custom_framework, custom_reasons = select_custom_story_framework(custom_inputs)
            reason_chips = "".join(f'<span class="badge badge-signal">{reason}</span>' for reason in custom_reasons)

            st.markdown(f"""
            <div style="font-size:0.86rem;color:var(--muted);line-height:1.7;margin-bottom:12px;">
              <strong>Khách hàng:</strong> {custom_inputs.get('gender','—')} · {custom_inputs.get('age','—')} tuổi ·
              {custom_inputs.get('occupation','—')} · {custom_inputs.get('persona','—')} · {custom_inputs.get('cluster','—')} ·
              Phong cách: {custom_inputs.get('style','—')} · Dịp mua suy ra: {custom_inputs.get('purchase_occasion','—')} ·
              Ngân sách: {custom_inputs.get('budget','—')}
            </div>
            <div style="margin-bottom:12px;">{reason_chips}</div>
            """, unsafe_allow_html=True)

            if not api_key:
                st.warning("⚠️ Vui lòng thiết lập OPENAI_API_KEY để sinh bộ nội dung storytelling.")
            elif st.session_state.custom_story is None:
                try:
                    def custom_stream_gen():
                        yield from generate_custom_story_stream(
                            custom_inputs,
                            temperature=st.session_state.custom_retry_temp,
                        )

                    full_custom_story = st.write_stream(custom_stream_gen())
                    st.session_state.custom_story = full_custom_story
                except Exception as e:
                    st.error(f"❌ Lỗi khi gọi OpenAI API: {str(e)}")
            else:
                st.markdown(st.session_state.custom_story)

            st.markdown("---")
            act1, act2, act3 = st.columns(3)
            with act1:
                if st.button("🔄 Tạo lại content", use_container_width=True):
                    st.session_state.custom_story = None
                    st.session_state.custom_retry_temp = min(1.2, st.session_state.custom_retry_temp + 0.1)
                    st.rerun()
            with act2:
                if st.session_state.custom_story:
                    st.code(st.session_state.custom_story, language=None)
            with act3:
                prod_url = prod.get("url", "")
                if prod_url:
                    st.link_button("🔗 Xem SP trên PNJ", prod_url, use_container_width=True)
        else:
            # ── Comparison: Original description vs AI story ──────────────────
            orig_col, story_col = st.columns([1, 1], gap="large")

            with orig_col:
                st.markdown('<div class="compare-label">📄 Mô tả gốc từ PNJ</div>', unsafe_allow_html=True)
                original_desc = prod.get("short_description", "").strip()
                if not original_desc:
                    original_desc = "(Không có mô tả gốc)"
                st.markdown(
                    f'<div class="original-desc">{original_desc}</div>',
                    unsafe_allow_html=True,
                )

            with story_col:
                st.markdown(f'<div class="compare-label">✨ Câu chuyện cá nhân hóa — {fw["icon"]} {fw["name"]}</div>', unsafe_allow_html=True)

                if st.session_state.story is None and api_key:
                    try:
                        cust_data = get_customer(customers_df, st.session_state.story_customer_id)

                        def stream_gen():
                            yield from generate_story_stream(cust_data, prod, fw_key, st.session_state.retry_temp)

                        full_story = st.write_stream(stream_gen())
                        st.session_state.story = full_story
                        st.session_state.zalo_msg = None

                    except Exception as e:
                        st.error(f"❌ Lỗi khi gọi OpenAI API: {str(e)}")

                elif st.session_state.story:
                    st.markdown(
                        f'<div class="story-text">{st.session_state.story}</div>',
                        unsafe_allow_html=True,
                    )
                elif not api_key:
                    st.warning("⚠️ Vui lòng thiết lập OPENAI_API_KEY để sinh câu chuyện.")

            st.markdown("---")

            # Action buttons
            act1, act2, act3 = st.columns(3)
            with act1:
                if st.button("🔄 Tạo lại", use_container_width=True):
                    st.session_state.story = None
                    st.session_state.zalo_msg = None
                    st.session_state.retry_temp = min(1.2, st.session_state.retry_temp + 0.1)
                    st.rerun()
            with act2:
                if st.session_state.story:
                    st.code(st.session_state.story, language=None)
            with act3:
                prod_url = prod.get("url", "")
                if prod_url:
                    st.link_button("🔗 Xem SP trên PNJ", prod_url, use_container_width=True)

            # ── Zalo Message Panel ─────────────────────────────────────────────
            if st.session_state.story and api_key:
                st.markdown("""
                <div class="zalo-panel">
                  <div class="zalo-header">
                    <span>💬 Tin nhắn Zalo cho nhân viên</span>
                    <span class="zalo-badge">VĂN NÓI</span>
                  </div>
                """, unsafe_allow_html=True)

                zalo_col, _ = st.columns([3, 2])
                with zalo_col:
                    if st.session_state.zalo_msg is None:
                        try:
                            cust_data = get_customer(customers_df, st.session_state.story_customer_id)

                            def zalo_stream_gen():
                                yield from generate_zalo_stream(
                                    cust_data, prod, fw_key,
                                    st.session_state.story,
                                    temperature=0.80,
                                )

                            full_zalo = st.write_stream(zalo_stream_gen())
                            st.session_state.zalo_msg = full_zalo

                        except Exception as e:
                            st.error(f"❌ Lỗi sinh tin nhắn Zalo: {str(e)}")
                    else:
                        st.markdown(
                            f'<div class="zalo-bubble">{st.session_state.zalo_msg}</div>',
                            unsafe_allow_html=True,
                        )

                    if st.session_state.zalo_msg:
                        st.markdown(
                            '<div class="zalo-hint">📋 Copy đoạn dưới để dán vào Zalo:</div>',
                            unsafe_allow_html=True,
                        )
                        st.code(st.session_state.zalo_msg, language=None)

                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ── Helper: fit reason per framework ──────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Tại Sao Chọn Phương Pháp Này?
# ═══════════════════════════════════════════════════════════════════════════════
with tab_why:
    cid = st.session_state.get("current_customer_id")
    cust_why = get_customer(customers_df, cid) if cid else None

    if not cust_why:
        st.info("← Hãy chọn một khách hàng trong tab **Danh Mục & Câu Chuyện** trước.")
    else:
        exp = get_selection_explanation(cust_why)
        fw_exp = exp["framework"]
        badge_cls = {
            "Hero's Journey": "badge-hero",
            "Golden Circle": "badge-golden",
            "Emotional Branding": "badge-emotional",
        }.get(exp["framework_key"], "badge-hero")
        persona_icon = get_persona_icon(exp["persona"])

        # ── Header ──
        st.markdown(f"""
        <div style="background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px 24px;margin-bottom:20px;">
          <div style="display:flex;align-items:center;gap:14px;">
            <div style="font-size:2.5rem">{persona_icon}</div>
            <div>
              <div style="font-family:'Playfair Display',serif;font-size:1.25rem;font-weight:700;color:#1A1A1A">
                Phân tích lựa chọn framework cho khách hàng {cid}
              </div>
              <span class="badge {badge_cls}" style="margin-top:4px">
                {fw_exp['icon']} {exp['framework_key']} được chọn
              </span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        info_col, rules_col = st.columns([1, 1], gap="large")

        # ── Cột trái: Thông tin khách hàng ──
        with info_col:
            st.markdown("#### 1. Nhận diện khách hàng")
            st.markdown(f"""
            | Trường | Giá trị |
            |--------|---------|
            | Persona | **{exp['persona']}** |
            | Cluster | {exp['cluster']} |
            | Phong cách | {exp['style']} |
            | Ưa thích | {exp['preferred_type']} / {exp['material']} |
            | Phân khúc | {exp['segment']} |
            """)

            if exp["signals"]:
                st.markdown("**Tín hiệu hành vi đang active:**")
                for s in exp["signals"]:
                    st.markdown(f"<span class='badge badge-signal'>{s}</span>", unsafe_allow_html=True)

        # ── Cột phải: Sơ đồ quyết định ──
        with rules_col:
            st.markdown("#### 2. Sơ đồ quyết định (theo thứ tự ưu tiên)")

            for rule in DECISION_RULES:
                triggered = (rule["priority"] == exp["triggered_priority"])
                row_cls = "rule-triggered" if triggered else "rule-normal"
                check = "✅" if triggered else "○"
                result_color = fw_exp["color"] if triggered else "#aaa"
                st.markdown(f"""
                <div class="rule-row {row_cls}">
                  <span class="rule-check">{check}</span>
                  <span class="rule-priority">#{rule['priority']}</span>
                  <span class="badge badge-rule-type">{rule['type']}</span>
                  <span class="rule-condition">{rule['condition']}</span>
                  <span class="rule-result" style="color:{result_color}">→ {rule['result']}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Lý do phù hợp ──
        reason_col, basis_col = st.columns([1, 1], gap="large")

        with reason_col:
            st.markdown("#### 3. Tại sao framework này phù hợp?")
            st.markdown(f"""
            <div style="background:#fff;border:1px solid var(--border);border-radius:10px;padding:16px;line-height:1.7;font-size:0.9rem;">
              {fw_exp.get('psychology', '')}
              <br/><br/>
              <span style="color:var(--gold);font-weight:600">Áp dụng cho khách hàng này:</span><br/>
              {_get_fit_reason(exp['framework_key'], exp['persona'])}
            </div>
            """, unsafe_allow_html=True)

        with basis_col:
            st.markdown("#### 4. Lưu ý khi kể chuyện")
            st.markdown(f"""
            <div style="background:#fff;border:1px solid var(--border);border-radius:10px;padding:16px;line-height:1.7;font-size:0.9rem;">
              <div style="margin-bottom:10px;">
                <span style="color:var(--gold);font-weight:600">Giọng điệu:</span><br/>
                {fw_exp.get('tone', '')}
              </div>
              <div>
                <span style="color:#C2185B;font-weight:600">Tránh:</span><br/>
                {fw_exp.get('avoid', '')}
              </div>
            </div>
            """, unsafe_allow_html=True)


def _get_fit_reason(framework_key: str, persona: str) -> str:
    reasons = {
        "Hero's Journey": f"Khách hàng với persona <em>'{persona}'</em> đang tìm kiếm sự tự công nhận. Câu chuyện Hero's Journey chạm đúng vào cảm giác 'mình xứng đáng được điều này' mà không cần ai khác công nhận.",
        "Golden Circle": f"Khách hàng với persona <em>'{persona}'</em> đang ở khoảnh khắc trọng đại. Họ cần câu chuyện bắt đầu từ ý nghĩa sâu xa — WHY — không phải từ thông số sản phẩm.",
        "Emotional Branding": f"Khách hàng với persona <em>'{persona}'</em> đang mua cho người khác. Câu chuyện cần hướng hoàn toàn vào người nhận — phẩm chất của họ, khoảnh khắc trao quà, cảm xúc họ sẽ có.",
    }
    return reasons.get(framework_key, "")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Hướng Dẫn 3 Phương Pháp Storytelling
# ═══════════════════════════════════════════════════════════════════════════════
with tab_guide:
    st.markdown("""
    <div style="background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px 24px;margin-bottom:24px;">
      <div style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;color:#1A1A1A;margin-bottom:8px;">
        Storytelling trong bán hàng trang sức — Tại sao lại quan trọng?
      </div>
      <div style="font-size:0.9rem;line-height:1.8;color:var(--text);">
        Khách hàng mua trang sức không chỉ vì vẻ đẹp của sản phẩm — họ mua vì <strong>câu chuyện mà sản phẩm đó kể</strong>.
        Nghiên cứu cho thấy <strong>95% quyết định mua hàng được đưa ra bởi cảm xúc</strong>, không phải lý trí.
        Thay vì liệt kê thông số kỹ thuật, tư vấn viên có thể dùng 3 framework dưới đây để <em>chạm đúng cảm xúc</em>
        của từng nhóm khách hàng khác nhau.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Comparison table
    st.markdown("### So sánh 3 phương pháp")
    st.markdown("""
    | Phương pháp | Dành cho | Tâm điểm | Cấu trúc | Giọng điệu |
    |---|---|---|---|---|
    | ⚔️ **Hero's Journey** | Người thích tự thưởng | Hành trình & thành tựu cá nhân | Ordinary World → Call → Transformation → Reward | Ấm, tôn trọng, không hào nhoáng |
    | ⭕ **Golden Circle** | Cầu hôn / Kỷ niệm | Ý nghĩa của tình yêu & cam kết | WHY → HOW → WHAT | Sâu lắng, thơ, trang trọng |
    | 💝 **Emotional Branding** | Mua quà tặng | Người nhận quà | Identity → Connection → Symbol → Memory | Ấm áp, tập trung vào người nhận |
    """)

    st.markdown("---")

    # Detailed cards for each framework
    fw_card_styles = {
        "Hero's Journey": "fw-card-hero",
        "Golden Circle": "fw-card-golden",
        "Emotional Branding": "fw-card-emotional",
    }

    for fw_key, fw_data in FRAMEWORKS.items():
        card_cls = fw_card_styles.get(fw_key, "")
        structure_html = fw_data.get('structure', '').replace('\n', '<br>')
        example_html = fw_data.get('example', '').replace('\n\n', '<br><br>').replace('\n', ' ')

        st.markdown(f"""
        <div class="fw-card {card_cls}">
          <div class="fw-card-title" style="color:{fw_data['color']}">
            {fw_data['icon']} {fw_data['name']} — {fw_data['short_desc']}
          </div>
          <div style="display:flex;gap:24px;margin-top:16px;">
            <div style="flex:1;min-width:0;">
              <div class="fw-section-label">Dành cho ai?</div>
              <div style="font-size:0.88rem;line-height:1.6;margin-bottom:12px;">{_format_target_personas(fw_data.get('target_persona', []))}</div>
              <div class="fw-section-label">Cơ sở tâm lý</div>
              <div style="font-size:0.88rem;line-height:1.7;margin-bottom:12px;">{fw_data.get('psychology', '')}</div>
              <div class="fw-section-label">Cấu trúc bắt buộc</div>
              <div style="font-size:0.85rem;line-height:1.7;background:#f9f9f9;padding:10px 12px;border-radius:8px;">{structure_html}</div>
            </div>
            <div style="flex:1;min-width:0;">
              <div class="fw-section-label">Giọng điệu</div>
              <div style="font-size:0.88rem;line-height:1.6;margin-bottom:12px;">{fw_data.get('tone', '')}</div>
              <div class="fw-section-label">Tránh</div>
              <div style="font-size:0.88rem;line-height:1.6;color:#C2185B;margin-bottom:12px;">{fw_data.get('avoid', '')}</div>
              <div class="fw-section-label">Ví dụ câu chuyện mẫu</div>
              <div class="fw-example">{example_html}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
