import os
import re
from html import escape

import pandas as pd
import streamlit as st


# --------------------------------------------------
# App configuration
# --------------------------------------------------
st.set_page_config(
    page_title="HCI Systematic Review Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Constants
# --------------------------------------------------
TEAM_MAPPING = {
    "Select your name...": None,
    "Aravind (Member A) - Pool 1": "Pool_1_Reviewer_A.csv",
    "Joel (Member B) - Pool 1": "Pool_1_Reviewer_B.csv",
    "Chris (Member C) - Pool 2": "Pool_2_Reviewer_C.csv",
    "Greg (Member D) - Pool 2": "Pool_2_Reviewer_D.csv",
}

DECISION_OPTIONS = ["Include", "For Consideration", "Exclude"]
YEAR_MIN = 2021
YEAR_MAX = 2026

INCLUSION_CRITERIA = [
    "Venue Quality: Peer-reviewed empirical study OR taxonomy paper published in a recognised HCI or Computer Science venue (ACM, IEEE, or Scopus-indexed journal or conference proceedings).",
    "Interaction Modality: Primary or significant focus on conversational interaction (voice or text) or adaptive AI interfaces; studies combining conversational and GUI elements are included where the conversational component is a substantive focus of analysis.",
    "Outcome Measurement: Reports measurable user behavioural outcomes (e.g., trust, data disclosure, engagement, autonomy).",
    f"Temporal Boundary: Published between {YEAR_MIN} - {YEAR_MAX}.",
    "Language: Full text available in English.",
]

EXCLUSION_CRITERIA = [
    "Legacy Interfaces: Traditional GUI-based dark patterns without a conversational or AI-adaptive component.",
    "Pure Technical/NLP: Pure NLP algorithmic papers evaluating model weights without human interaction.",
    "Pure Theory: Purely theoretical AI ethics papers lacking empirical interface evaluation.",
    "Non-Interactive AI: Non-interactive AI systems (e.g., static image generation).",
]

HIGHLIGHT_PATTERNS = {
    "modality": {
        "pattern": r"\b(llm|llms|chatbot|chatbots|conversational|dialogue|gpt|voice assistant|ai assistant|large language model|generative ai|genai|natural language interface|speech interface|multimodal|human-ai|assistant|virtual agent|agentic|embodied|persona|anthropomorphism)\b",
        "label": "Modality",
        "style": "background-color:#ede9fe;color:#5b21b6;",
    },
    "phenomenon": {
        "pattern": r"\b(dark pattern|dark patterns|deceptive|deception|manipulation|persuasion|persuasive|sycophancy|nudge|nudging|coercion|misleading|obfuscation|trickery|hidden costs|forced continuity|social engineering|algorithmic influence|influence|trust calibration|overtrust)\b",
        "label": "Dark pattern",
        "style": "background-color:#fee2e2;color:#b91c1c;",
    },
    "empirical": {
        "pattern": r"\b(user study|empirical|experiment|trial|participants|survey|interview|qualitative|quantitative|observational|trust|autonomy|agency|behavior|behaviour|engagement|disclosure|privacy|satisfaction|human-centered|evaluation|ux|user experience|decision-making)\b",
        "label": "Empirical",
        "style": "background-color:#dcfce7;color:#166534;",
    },
    "exclusion": {
        "pattern": r"\b(accuracy|f1-score|perplexity|loss function|training data|dataset|architecture|latency|performance metrics|static image|legacy gui|traditional web|theoretical framework|literature review|systematic review|survey paper|without human|purely technical)\b",
        "label": "Exclusion signal",
        "style": "background-color:#ffedd5;color:#c2410c;",
    },
}


# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        .main-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: inherit;
            padding: 0.2rem 0;
        }

        .subtle-text {
            color: #9ca3af;
            font-size: 0.95rem;
            margin-bottom: 1rem;
            padding: 0.3rem 0;
        }

        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(229, 231, 235, 0.2);
            border-radius: 14px;
            padding: 1.2rem 1.3rem;
            margin-bottom: 1.2rem;
        }

        .soft-card {
            background: rgba(248, 250, 252, 0.05);
            border: 1px solid rgba(229, 231, 235, 0.2);
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            margin-bottom: 1.2rem;
        }

        .section-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #9ca3af;
            font-weight: 700;
            margin-bottom: 0.7rem;
            padding: 0.3rem 0;
        }

        .paper-title {
            font-size: 1.35rem;
            font-weight: 700;
            line-height: 1.5;
            margin-bottom: 0.8rem;
            margin-top: 0.3rem;
            color: inherit;
            padding: 0.2rem 0;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }

        .meta-line {
            color: #d1d5db;
            font-size: 0.96rem;
            line-height: 1.8;
            margin-bottom: 0.5rem;
            padding: 0.15rem 0;
        }

        .chip {
            display: inline-block;
            padding: 0.35rem 0.75rem;
            margin: 0.25rem 0.5rem 0.25rem 0;
            border-radius: 999px;
            background: rgba(243, 244, 246, 0.1);
            border: 1px solid rgba(229, 231, 235, 0.2);
            font-size: 0.83rem;
            color: #d1d5db;
            white-space: nowrap;
        }

        .criterion-good, .criterion-warn, .criterion-bad, .criterion-neutral {
            border-radius: 12px;
            padding: 1rem 1.1rem;
            border: 1px solid #e5e7eb;
            min-height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .criterion-good {
            background: rgba(236, 253, 245, 0.15);
            border-color: rgba(187, 247, 208, 0.3);
        }

        .criterion-warn {
            background: rgba(255, 251, 235, 0.15);
            border-color: rgba(253, 230, 138, 0.3);
        }

        .criterion-bad {
            background: rgba(254, 242, 242, 0.15);
            border-color: rgba(254, 202, 202, 0.3);
        }

        .criterion-neutral {
            background: rgba(248, 250, 252, 0.08);
            border-color: rgba(229, 231, 235, 0.2);
        }

        .criterion-title {
            font-size: 0.8rem;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-weight: 700;
            margin-bottom: 0.6rem;
            padding: 0.2rem 0;
        }

        .criterion-value {
            font-size: 1rem;
            font-weight: 700;
            color: inherit;
            margin-bottom: 0.5rem;
            padding: 0.1rem 0;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }

        .criterion-note {
            font-size: 0.9rem;
            color: #9ca3af;
            padding: 0.1rem 0;
            line-height: 1.4;
        }

        .abstract-box {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(229, 231, 235, 0.2);
            border-radius: 14px;
            padding: 1.3rem 1.4rem;
            line-height: 1.85;
            font-size: 1rem;
            margin-bottom: 1.2rem;
        }

        .highlight-pill {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 0.4rem;
            margin-bottom: 0.4rem;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .footer-note {
            color: #9ca3af;
            font-size: 0.87rem;
            margin-top: 1rem;
            padding: 0.4rem 0;
            line-height: 1.5;
        }

        div[data-testid="stMetric"] {
            background: rgba(248, 250, 252, 0.08);
            border: 1px solid rgba(229, 231, 235, 0.2);
            border-radius: 12px;
            padding: 1rem;
        }

        .stButton > button {
            height: 3.2rem;
            font-weight: 700;
            border-radius: 12px;
            padding: 0.8rem 1.5rem;
        }

        .stProgress > div > div > div {
            margin-bottom: 0.8rem;
        }

        /* Expander padding */
        .streamlit-expanderHeader {
            padding: 1rem 0;
        }

        /* Column spacing */
        .stColumn {
            padding: 0.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Helpers
# --------------------------------------------------
@st.cache_data(ttl=2)
def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    if "Reviewer_Decision" not in df.columns:
        df.insert(0, "Reviewer_Decision", "Pending")
    else:
        df["Reviewer_Decision"] = df["Reviewer_Decision"].fillna("Pending")
    return df


def save_decision(df: pd.DataFrame, row_index: int, decision: str, file_path: str) -> None:
    df.at[row_index, "Reviewer_Decision"] = decision
    df.to_csv(file_path, index=False)


def clean_text(value, fallback="N/A") -> str:
    if pd.isna(value):
        return fallback
    text = str(value).strip()
    return fallback if text == "" or text.lower() == "nan" else text


def parse_tags(value) -> list[str]:
    text = clean_text(value, fallback="")
    if not text:
        return []
    return [tag.strip() for tag in re.split(r"[;,]", text) if tag.strip()]


def badge_html(text: str) -> str:
    return f'<span class="chip">{escape(text)}</span>'


def highlight_keywords(text) -> str:
    if not isinstance(text, str) or not text.strip():
        return "<span class='subtle-text'>No abstract available.</span>"

    safe_text = escape(text)

    for config in HIGHLIGHT_PATTERNS.values():
        pattern = config["pattern"]
        style = config["style"]

        def repl(match):
            matched = match.group(0)
            return (
                f"<span style=\"{style} padding:0.12rem 0.28rem; "
                f"border-radius:0.35rem; font-weight:600;\">{matched}</span>"
            )

        safe_text = re.sub(pattern, repl, safe_text, flags=re.IGNORECASE)

    return safe_text


def get_year_status(year_value):
    year = pd.to_numeric(year_value, errors="coerce")
    if pd.isna(year):
        return "Unknown", "bad", "Year unavailable"
    year = int(year)
    if YEAR_MIN <= year <= YEAR_MAX:
        return str(year), "good", f"Within {YEAR_MIN}–{YEAR_MAX}"
    return str(year), "bad", f"Outside {YEAR_MIN}–{YEAR_MAX}"


def get_item_type_status(item_type: str):
    item = clean_text(item_type, "Unknown")
    lowered = item.lower()

    if any(term in lowered for term in ["journal article", "conference paper", "proceedings", "article"]):
        return item, "good", "Likely suitable publication type"
    if item == "Unknown":
        return item, "warn", "Check manually"
    return item, "neutral", "Needs reviewer judgement"


def get_venue_status(venue: str):
    venue_clean = clean_text(venue, "Unknown venue")
    if venue_clean == "Unknown venue":
        return venue_clean, "warn", "Venue missing"
    return venue_clean, "neutral", "Use as a quick context cue"


def render_criterion_card(title: str, value: str, note: str, status: str):
    class_name = {
        "good": "criterion-good",
        "warn": "criterion-warn",
        "bad": "criterion-bad",
        "neutral": "criterion-neutral",
    }.get(status, "criterion-neutral")

    st.markdown(
        f"""
        <div class="{class_name}">
            <div class="criterion-title">{escape(title)}</div>
            <div class="criterion-value">{escape(value)}</div>
            <div class="criterion-note">{escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_legend():
    legend_parts = [
        ('<span class="highlight-pill" style="background:#ede9fe;color:#5b21b6;border-color:#ddd6fe;">Modality</span>'),
        ('<span class="highlight-pill" style="background:#fee2e2;color:#b91c1c;border-color:#fecaca;">Dark pattern</span>'),
        ('<span class="highlight-pill" style="background:#dcfce7;color:#166534;border-color:#bbf7d0;">Empirical</span>'),
        ('<span class="highlight-pill" style="background:#ffedd5;color:#c2410c;border-color:#fdba74;">Exclusion signal</span>'),
    ]
    st.markdown("".join(legend_parts), unsafe_allow_html=True)


# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.title("Reviewer")
    selected_user = st.selectbox("Who is screening?", list(TEAM_MAPPING.keys()))
    st.markdown("---")
    st.caption("Tip: work top to bottom. Use the criteria panel only when the abstract is ambiguous.")

if TEAM_MAPPING[selected_user] is None:
    st.markdown("")
    st.markdown("")
    st.markdown('<div class="main-title">Systematic Review Phase 2</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtle-text">Select your name in the sidebar to load your assigned screening file.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

target_file = TEAM_MAPPING[selected_user]
reviewer_name = selected_user.split(" (")[0]

if not os.path.exists(target_file):
    st.error(f"File not found: {target_file}")
    st.stop()

df = load_data(target_file)
pending_papers = df[df["Reviewer_Decision"] == "Pending"]

if pending_papers.empty:
    st.balloons()
    st.success(f"Screening complete, {reviewer_name}.")
    st.write(f"All decisions have been saved to `{target_file}`.")
    st.stop()

current_index = pending_papers.index[0]
row = df.loc[current_index]

total_papers = len(df)
screened_count = total_papers - len(pending_papers)
progress_ratio = screened_count / total_papers if total_papers else 0


# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("")
st.markdown(f'<div class="main-title">Screening Portal</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="subtle-text">{escape(reviewer_name)} · reviewing 1 paper at a time · autosaving to {escape(target_file)}</div>',
    unsafe_allow_html=True,
)
st.markdown("")

top_a, top_b, top_c = st.columns([1.2, 1, 1])
with top_a:
    st.progress(progress_ratio, text=f"Progress: {screened_count} / {total_papers} screened")
with top_b:
    st.metric("Remaining", len(pending_papers))
with top_c:
    st.metric("Completed", screened_count)

st.markdown("")


# --------------------------------------------------
# Decision snapshot
# --------------------------------------------------
st.markdown('<div class="section-label">Decision snapshot</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

year_value, year_status, year_note = get_year_status(row.get("Publication Year"))
venue_value, venue_status, venue_note = get_venue_status(row.get("Publication Title"))
type_value, type_status, type_note = get_item_type_status(row.get("Item Type"))

with col1:
    render_criterion_card("Publication year", year_value, year_note, year_status)
with col2:
    render_criterion_card("Venue", venue_value[:70] + ("..." if len(venue_value) > 70 else ""), venue_note, venue_status)
with col3:
    render_criterion_card("Item type", type_value, type_note, type_status)


# --------------------------------------------------
# Paper details
# --------------------------------------------------
title = clean_text(row.get("Title"), "No title available")
authors = clean_text(row.get("Author"), "N/A")
manual_tags = parse_tags(row.get("Manual Tags"))
decision_so_far = clean_text(row.get("Reviewer_Decision"), "Pending")

st.markdown(
    f"""
    <div class="card">
        <div class="section-label">Current paper</div>
        <div class="paper-title">{escape(title)}</div>
        <div class="meta-line"><strong>Authors:</strong> {escape(authors)}</div>
        <div class="meta-line"><strong>Status:</strong> {escape(decision_so_far)}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if manual_tags:
    tags_html = "".join(badge_html(tag) for tag in manual_tags)
    st.markdown(
        f"""
        <div class="soft-card">
            <div class="section-label">Manual tags</div>
            {tags_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# Abstract
# --------------------------------------------------
st.markdown('<div class="section-label">Abstract</div>', unsafe_allow_html=True)
render_legend()

abstract_text = row.get("Abstract Note", "")
st.markdown(
    f'<div class="abstract-box">{highlight_keywords(abstract_text)}</div>',
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Criteria panel
# --------------------------------------------------
with st.expander("View inclusion and exclusion criteria", expanded=False):
    left, right = st.columns(2)

    with left:
        st.markdown("#### Inclusion")
        for item in INCLUSION_CRITERIA:
            st.markdown(f"- {item}")

    with right:
        st.markdown("#### Exclusion")
        for item in EXCLUSION_CRITERIA:
            st.markdown(f"- {item}")


# --------------------------------------------------
# Decision actions
# --------------------------------------------------
st.markdown("")
st.markdown('<div class="section-label">Decision</div>', unsafe_allow_html=True)
st.caption("Choose the closest screening outcome. The file updates immediately after selection.")

b1, b2, b3 = st.columns(3)

with b1:
    if st.button("Include", use_container_width=True, type="primary"):
        save_decision(df, current_index, "Include", target_file)
        st.rerun()

with b2:
    if st.button("For Consideration", use_container_width=True):
        save_decision(df, current_index, "For Consideration", target_file)
        st.rerun()

with b3:
    if st.button("Exclude", use_container_width=True):
        save_decision(df, current_index, "Exclude", target_file)
        st.rerun()

st.markdown("")
st.markdown(
    '<div class="footer-note">Review flow: snapshot → title/authors/tags → abstract → criteria check only if needed → decision.</div>',
    unsafe_allow_html=True,
)
