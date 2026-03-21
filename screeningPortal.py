import os
import re
import sys
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
# Get the directory where this script is located
if __file__:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    SCRIPT_DIR = os.getcwd()

TEAM_MAPPING = {
    "Select your name...": None,
    "Aravind (Member A) - Pool 1": os.path.join(SCRIPT_DIR, "Pool_1_Reviewer_A.csv"),
    "Joel (Member B) - Pool 1": os.path.join(SCRIPT_DIR, "Pool_1_Reviewer_B.csv"),
    "Chris (Member C) - Pool 2": os.path.join(SCRIPT_DIR, "Pool_2_Reviewer_C.csv"),
    "Greg (Member D) - Pool 2": os.path.join(SCRIPT_DIR, "Pool_2_Reviewer_D.csv"),
}

RESOLUTION_FILE = os.path.join(SCRIPT_DIR, "Conflict_Resolution_Log.csv")

DECISION_OPTIONS = ["Include", "For Consideration", "Exclude"]
YEAR_MIN = 2021
YEAR_MAX = 2026

INCLUSION_CRITERIA = [
    "**Study type:** Peer-reviewed empirical study OR taxonomy/review paper directly relevant to conversational manipulation, deception, or dark patterns in AI. For taxonomy papers, outcome measurement not required.",
    "**Publication source:** ACM, IEEE, Scopus-indexed venues, or recognised HCI venues (CHI, TOCHI, UIST, UbiComp, DIS, CSCW, PACM HCI, IJHCS, HCI Taylor & Francis). Interdisciplinary papers from Psychology, Cognitive Science, or Social Science eligible if examining conversational AI. arXiv only if peer-reviewed version confirmed or under review.",
    "**Interaction focus:** Primary component is conversational AI, chatbots, voice assistants, LLM interfaces, or adaptive AI with conversational interaction.",
    "**Mixed interfaces:** GUI + conversational eligible only if conversational is substantive focus, not merely incidental.",
    "**Outcomes:** At least one observable user outcome (trust, disclosure, compliance, engagement, autonomy, decision-making, etc.). Required for empirical studies only.",
    f"**Date range:** Published {YEAR_MIN}–{YEAR_MAX} inclusive.",
    "**Language:** Full text in English.",
]

EXCLUSION_CRITERIA = [
    "**Legacy interfaces:** Traditional GUI dark patterns without conversational/adaptive AI; conversational element peripheral to core evaluation.",
    "**Pure technical:** Model architecture, training, benchmarks, prompt engineering, or optimisation without user/human-subject evaluation.",
    "**Pure theory:** Conceptual ethics, policy, or opinion without empirical interface analysis or structured taxonomy contribution.",
    "**Non-interactive AI:** No live user interaction (e.g., static image generation, offline classification, batch processing).",
    "**No outcomes:** System/prototype described without user-facing outcomes (empirical studies only; taxonomy papers exempt).",
    "**Ineligible types:** Abstracts only, editorials, theses, patents, slides, grey literature. Unconfirmed arXiv preprints without peer-reviewed publication excluded.",
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
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }
        .main-title { font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; padding: 1.5rem 0 0.2rem 0; }
        .subtle-text { color: #9ca3af; font-size: 0.95rem; margin-bottom: 1rem; padding: 0.5rem 0 0.3rem 0; }
        .card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(229, 231, 235, 0.2); border-radius: 14px; padding: 1.2rem 1.3rem; margin-bottom: 1.2rem; }
        .soft-card { background: rgba(248, 250, 252, 0.05); border: 1px solid rgba(229, 231, 235, 0.2); border-radius: 14px; padding: 1.1rem 1.3rem; margin-bottom: 1.2rem; }
        .section-label { font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.04em; color: #9ca3af; font-weight: 700; margin-bottom: 0.7rem; padding: 0.3rem 0; }
        .paper-title { font-size: 1.35rem; font-weight: 700; line-height: 1.5; margin-bottom: 0.8rem; margin-top: 0.3rem; word-wrap: break-word; overflow-wrap: break-word; }
        .meta-line { color: #d1d5db; font-size: 0.96rem; line-height: 1.8; margin-bottom: 0.5rem; padding: 0.15rem 0; }
        .chip { display: inline-block; padding: 0.35rem 0.75rem; margin: 0.25rem 0.5rem 0.25rem 0; border-radius: 999px; background: rgba(243, 244, 246, 0.1); border: 1px solid rgba(229, 231, 235, 0.2); font-size: 0.83rem; color: #d1d5db; white-space: nowrap; }
        .criterion-good, .criterion-warn, .criterion-bad, .criterion-neutral { border-radius: 12px; padding: 1rem 1.1rem; border: 1px solid #e5e7eb; min-height: 110px; display: flex; flex-direction: column; justify-content: space-between; }
        .criterion-good { background: rgba(236, 253, 245, 0.15); border-color: rgba(187, 247, 208, 0.3); }
        .criterion-warn { background: rgba(255, 251, 235, 0.15); border-color: rgba(253, 230, 138, 0.3); }
        .criterion-bad { background: rgba(254, 242, 242, 0.15); border-color: rgba(254, 202, 202, 0.3); }
        .criterion-neutral { background: rgba(248, 250, 252, 0.08); border-color: rgba(229, 231, 235, 0.2); }
        .criterion-title { font-size: 0.8rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 700; margin-bottom: 0.6rem; padding: 0.2rem 0; }
        .criterion-value { font-size: 1rem; font-weight: 700; margin-bottom: 0.5rem; padding: 0.1rem 0; word-wrap: break-word; overflow-wrap: break-word; }
        .criterion-note { font-size: 0.9rem; color: #9ca3af; padding: 0.1rem 0; line-height: 1.4; }
        .abstract-box { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(229, 231, 235, 0.2); border-radius: 14px; padding: 1.3rem 1.4rem; line-height: 1.85; font-size: 1rem; margin-bottom: 1.2rem; }
        .highlight-pill { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 8px; font-size: 0.8rem; font-weight: 600; margin-right: 0.4rem; margin-bottom: 0.4rem; border: 1px solid transparent; white-space: nowrap; }
        .footer-note { color: #9ca3af; font-size: 0.87rem; margin-top: 1rem; padding: 0.4rem 0; line-height: 1.5; }
        div[data-testid="stMetric"] { background: rgba(248, 250, 252, 0.08); border: 1px solid rgba(229, 231, 235, 0.2); border-radius: 12px; padding: 1rem; }
        .stButton > button { height: 3.2rem; font-weight: 700; border-radius: 12px; padding: 0.8rem 1.5rem; }
        .stProgress > div > div > div { margin-bottom: 0.8rem; }
        .streamlit-expanderHeader { padding: 1rem 0; }
        .stColumn { padding: 0.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Helpers
# --------------------------------------------------
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


def save_conflict_resolution(pool: str, title: str, author: str, pub_title: str, v1: str, v2: str, decision: str, rationale: str) -> None:
    if os.path.exists(RESOLUTION_FILE):
        df_res = pd.read_csv(RESOLUTION_FILE)
    else:
        df_res = pd.DataFrame(columns=['Pool', 'Title', 'Author', 'Publication Title', 'Vote_1', 'Vote_2', 'Final_Decision', 'Rationale'])

    mask = df_res['Title'] == title
    if mask.any():
        idx = df_res.index[mask].tolist()[0]
        df_res.at[idx, 'Final_Decision'] = decision
        df_res.at[idx, 'Rationale'] = rationale
        df_res.at[idx, 'Vote_1'] = v1
        df_res.at[idx, 'Vote_2'] = v2
    else:
        new_row = pd.DataFrame([{
            'Pool': pool, 'Title': title, 'Author': author, 'Publication Title': pub_title,
            'Vote_1': v1, 'Vote_2': v2, 'Final_Decision': decision, 'Rationale': rationale
        }])
        df_res = pd.concat([df_res, new_row], ignore_index=True)

    df_res.to_csv(RESOLUTION_FILE, index=False)


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
            return f"<span style=\"{style} padding:0.12rem 0.28rem; border-radius:0.35rem; font-weight:600;\">{matched}</span>"
        safe_text = re.sub(pattern, repl, safe_text, flags=re.IGNORECASE)
    return safe_text


def get_year_status(year_value):
    year = pd.to_numeric(year_value, errors="coerce")
    if pd.isna(year): return "Unknown", "bad", "Year unavailable"
    year = int(year)
    if YEAR_MIN <= year <= YEAR_MAX: return str(year), "good", f"Within {YEAR_MIN}–{YEAR_MAX}"
    return str(year), "bad", f"Outside {YEAR_MIN}–{YEAR_MAX}"


def get_item_type_status(item_type: str):
    item = clean_text(item_type, "Unknown")
    lowered = item.lower()
    if any(term in lowered for term in ["journal article", "conference paper", "proceedings", "article"]):
        return item, "good", "Likely suitable publication type"
    if item == "Unknown": return item, "warn", "Check manually"
    return item, "neutral", "Needs reviewer judgement"


def get_venue_status(venue: str):
    venue_clean = clean_text(venue, "Unknown venue")
    if venue_clean == "Unknown venue": return venue_clean, "warn", "Venue missing"
    return venue_clean, "neutral", "Use as a quick context cue"


def render_criterion_card(title: str, value: str, note: str, status: str):
    class_name = {"good": "criterion-good", "warn": "criterion-warn", "bad": "criterion-bad", "neutral": "criterion-neutral"}.get(status, "criterion-neutral")
    st.markdown(
        f"""
        <div class="{class_name}">
            <div class="criterion-title">{escape(title)}</div>
            <div class="criterion-value">{escape(value)}</div>
            <div class="criterion-note">{escape(note)}</div>
        </div>
        """, unsafe_allow_html=True
    )


def render_legend():
    legend_parts = [
        '<span class="highlight-pill" style="background:#ede9fe;color:#5b21b6;border-color:#ddd6fe;">Modality</span>',
        '<span class="highlight-pill" style="background:#fee2e2;color:#b91c1c;border-color:#fecaca;">Dark pattern</span>',
        '<span class="highlight-pill" style="background:#dcfce7;color:#166534;border-color:#bbf7d0;">Empirical</span>',
        '<span class="highlight-pill" style="background:#ffedd5;color:#c2410c;border-color:#fdba74;">Exclusion signal</span>',
    ]
    st.markdown("".join(legend_parts), unsafe_allow_html=True)


# --------------------------------------------------
# Sidebar & Routing
# --------------------------------------------------
with st.sidebar:
    st.title("Settings")
    app_mode = st.radio("Mode:", ["Individual Screening", "Conflict Resolution"])
    st.markdown("---")

    if app_mode == "Individual Screening":
        selected_user = st.selectbox("Who is screening?", list(TEAM_MAPPING.keys()))
        st.caption("Tip: work top to bottom. Use the criteria panel only when the abstract is ambiguous.")
    else:
        selected_pool = st.selectbox("Which pool to resolve?", ["Select a pool...", "Pool 1 (Aravind & Joel)", "Pool 2 (Chris & Greg)"])
        st.caption("Resolves disagreements and 'For Consideration' votes between reviewers.")

# --------------------------------------------------
# Data Processing (Branching Logic)
# --------------------------------------------------
if app_mode == "Individual Screening":
    if selected_user == "Select your name..." or TEAM_MAPPING.get(selected_user) is None:
        st.markdown('<div class="main-title">Systematic Review Phase 2</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtle-text">Select your name in the sidebar to load your assigned screening file.</div>', unsafe_allow_html=True)
        st.stop()

    target_file = TEAM_MAPPING.get(selected_user)
    reviewer_name = selected_user.split(" (")[0]

    if not os.path.exists(target_file):
        st.error(f"File not found: {target_file}")
        st.stop()

    df = load_data(target_file)
    pending_papers = df[df["Reviewer_Decision"] == "Pending"]

    if pending_papers.empty:
        st.balloons()
        st.success(f"Screening complete, {reviewer_name}.")
        st.stop()

    current_index = pending_papers.index[0]
    row = df.loc[current_index]

    total_items = len(df)
    completed_count = total_items - len(pending_papers)
    progress_ratio = completed_count / total_items if total_items else 0
    remaining_count = len(pending_papers)
    
    # "Go Back" logic for individual mode
    screened_papers = df[df["Reviewer_Decision"] != "Pending"]
    last_screened_index = screened_papers.index[-1] if not screened_papers.empty else None

else: # Conflict Resolution
    if selected_pool == "Select a pool...":
        st.markdown("")
        st.markdown("")
        st.markdown('<div class="main-title">Conflict Resolution</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtle-text">Select a pool in the sidebar to load disputed papers.</div>', unsafe_allow_html=True)
        st.stop()

    if "Pool 1" in selected_pool:
        f1, f2, rev1, rev2 = TEAM_MAPPING["Aravind (Member A) - Pool 1"], TEAM_MAPPING["Joel (Member B) - Pool 1"], "Aravind", "Joel"
    else:
        f1, f2, rev1, rev2 = TEAM_MAPPING["Chris (Member C) - Pool 2"], TEAM_MAPPING["Greg (Member D) - Pool 2"], "Chris", "Greg"

    if not os.path.exists(f1) or not os.path.exists(f2):
        st.error(f"Missing reviewer files for {selected_pool}. Ensure both CSVs are in the directory.")
        st.stop()

    df1, df2 = load_data(f1), load_data(f2)
    df_merged = pd.merge(df1, df2[['Title', 'Reviewer_Decision']], on='Title', suffixes=('_1', '_2'))
    
    # Filter constraints (Both voted, and they either disagree OR someone flagged for consideration)
    mask_conflict = (
        (df_merged['Reviewer_Decision_1'] != 'Pending') & 
        (df_merged['Reviewer_Decision_2'] != 'Pending') & 
        (
            (df_merged['Reviewer_Decision_1'] != df_merged['Reviewer_Decision_2']) | 
            (df_merged['Reviewer_Decision_1'] == 'For Consideration') | 
            (df_merged['Reviewer_Decision_2'] == 'For Consideration')
        )
    )
    conflicts_df = df_merged[mask_conflict].copy()

    if os.path.exists(RESOLUTION_FILE):
        res_df = pd.read_csv(RESOLUTION_FILE)
        resolved_titles = res_df[(res_df['Final_Decision'] == 'Include') | (res_df['Final_Decision'] == 'Exclude')]['Title'].tolist()
        pending_conflicts = conflicts_df[~conflicts_df['Title'].isin(resolved_titles)]
    else:
        pending_conflicts = conflicts_df

    if pending_conflicts.empty:
        st.balloons()
        st.success(f"All conflicts resolved for {selected_pool}!")
        if len(conflicts_df) > 0:
            st.write(f"Results saved to `{RESOLUTION_FILE}`.")
        st.stop()

    # Setup standard variables for the UI rendering block
    row = pending_conflicts.iloc[0]
    total_items = len(conflicts_df)
    remaining_count = len(pending_conflicts)
    completed_count = total_items - remaining_count
    progress_ratio = completed_count / total_items if total_items else 0


# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("")

# Render Go Back button ONLY in Individual Screening mode
if app_mode == "Individual Screening" and last_screened_index is not None:
    col_back, col_title, col_spacer = st.columns([0.8, 2, 1])
    with col_back:
        if st.button("← Go Back", use_container_width=True):
            df.at[last_screened_index, "Reviewer_Decision"] = "Pending"
            df.to_csv(target_file, index=False)
            st.rerun()

header_title = "Screening Portal" if app_mode == "Individual Screening" else "Conflict Resolution"
subtitle = f"{escape(reviewer_name)} · autosaving to {escape(target_file)}" if app_mode == "Individual Screening" else f"Arbitrating {selected_pool} · autosaving to {os.path.basename(RESOLUTION_FILE)}"

st.markdown(f'<div class="main-title">{header_title}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtle-text">{subtitle}</div>', unsafe_allow_html=True)
st.markdown("")

top_a, top_b, top_c = st.columns([1.2, 1, 1])
with top_a:
    st.progress(progress_ratio, text=f"Progress: {completed_count} / {total_items} complete")
with top_b:
    st.metric("Remaining", remaining_count)
with top_c:
    st.metric("Completed", completed_count)

st.markdown("")

# Display decision distribution for individual screening mode
if app_mode == "Individual Screening":
    include_count = len(df[df["Reviewer_Decision"] == "Include"])
    exclude_count = len(df[df["Reviewer_Decision"] == "Exclude"])
    for_consideration_count = len(df[df["Reviewer_Decision"] == "For Consideration"])
    
    st.markdown(
        f"""
        <div style="font-size: 1.2rem; font-weight: 600; letter-spacing: 0.02em; margin: 0.5rem 0;">
            <span style="color: #10b981;">✓ {include_count} Include</span> · 
            <span style="color: #ef4444;">✕ {exclude_count} Exclude</span> · 
            <span style="color: #f59e0b;">? {for_consideration_count} For Consideration</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

if app_mode == "Individual Screening":
    status_text = clean_text(row.get("Reviewer_Decision"), "Pending")
else:
    status_text = "Conflict / Flagged for Consideration"

st.markdown(
    f"""
    <div class="card">
        <div class="section-label">Current paper</div>
        <div class="paper-title">{escape(title)}</div>
        <div class="meta-line"><strong>Authors:</strong> {escape(authors)}</div>
        <div class="meta-line"><strong>Status:</strong> {escape(status_text)}</div>
    </div>
    """, unsafe_allow_html=True
)

# Highlight Disputed Votes for Conflict Resolution Mode
if app_mode == "Conflict Resolution":
    st.markdown(
        f"""
        <div class="criterion-warn" style="margin-bottom: 1.2rem; min-height: auto; padding: 1.2rem;">
            <div class="criterion-title">Disputed Votes</div>
            <div style="display: flex; gap: 2rem; margin-top: 0.5rem; font-size: 1.05rem;">
                <div><strong>{escape(rev1)} voted:</strong> {badge_html(row['Reviewer_Decision_1'])}</div>
                <div><strong>{escape(rev2)} voted:</strong> {badge_html(row['Reviewer_Decision_2'])}</div>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

if manual_tags:
    tags_html = "".join(badge_html(tag) for tag in manual_tags)
    st.markdown(
        f"""
        <div class="soft-card">
            <div class="section-label">Manual tags</div>
            {tags_html}
        </div>
        """, unsafe_allow_html=True
    )


# --------------------------------------------------
# Abstract
# --------------------------------------------------
st.markdown('<div class="section-label">Abstract</div>', unsafe_allow_html=True)
render_legend()

abstract_text = row.get("Abstract Note", "")
st.markdown(f'<div class="abstract-box">{highlight_keywords(abstract_text)}</div>', unsafe_allow_html=True)


# --------------------------------------------------
# Criteria panel
# --------------------------------------------------
with st.expander("View inclusion and exclusion criteria", expanded=False):
    left, right = st.columns(2)
    with left:
        st.markdown("#### Inclusion")
        for item in INCLUSION_CRITERIA: st.markdown(f"- {item}")
    with right:
        st.markdown("#### Exclusion")
        for item in EXCLUSION_CRITERIA: st.markdown(f"- {item}")


# --------------------------------------------------
# Decision actions
# --------------------------------------------------
st.markdown("")
st.markdown('<div class="section-label">Decision</div>', unsafe_allow_html=True)

if app_mode == "Individual Screening":
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

else:
    # Conflict Resolution Mode Actions
    st.caption("Provide a rationale, then make a final ruling. This writes directly to the Conflict Resolution Log.")
    rationale = st.text_input("Rationale (Required for final decision)", placeholder="e.g., Focus is primarily GUI, conversational aspect is tangential.")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Final Include", use_container_width=True, type="primary"):
            if not rationale.strip():
                st.warning("Please provide a rationale before saving.")
            else:
                save_conflict_resolution(selected_pool, row['Title'], row.get('Author', ''), row.get('Publication Title', ''), row['Reviewer_Decision_1'], row['Reviewer_Decision_2'], "Include", rationale)
                st.rerun()
    with c2:
        if st.button("Final Exclude", use_container_width=True):
            if not rationale.strip():
                st.warning("Please provide a rationale before saving.")
            else:
                save_conflict_resolution(selected_pool, row['Title'], row.get('Author', ''), row.get('Publication Title', ''), row['Reviewer_Decision_1'], row['Reviewer_Decision_2'], "Exclude", rationale)
                st.rerun()

st.markdown("")
st.markdown('<div class="footer-note">Review flow: snapshot → title/authors/tags → abstract → criteria check only if needed → decision.</div>', unsafe_allow_html=True)