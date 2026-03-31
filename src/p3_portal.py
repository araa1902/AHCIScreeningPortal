import streamlit as st
import pandas as pd
import os

# --- 1. App Configuration ---
st.set_page_config(page_title="Phase 3: Full-Text & Quality Assessment", layout="wide")

# --- 2. Team & Setup ---
TEAM = ["Select Reviewer...", "Aravind", "Joel", "Chris", "Greg"]

EXCLUSION_REASONS = [
    "Select a reason...",
    "Legacy interfaces: Traditional GUI only",
    "Pure technical: No human-subject evaluation",
    "Pure theory: No empirical interface analysis",
    "Non-interactive AI: No live user interaction",
    "Insufficient outcomes: No measurable behavioral metrics",
    "Non-eligible type: Abstract only, thesis, grey literature"
]

st.sidebar.title("Phase 3 Authentication")
current_user = st.sidebar.selectbox("Active Reviewer", TEAM)

if current_user == "Select Reviewer...":
    st.title("Phase 3: Full-Text Review & Quality Assessment")
    st.info("Please select your reviewer profile to access the portal.")
    st.stop()

# --- 3. Data Management ---
# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(project_root, "data", "screening", "Phase3_Tracker.csv")

if not os.path.exists(DATA_FILE):
    st.warning(f"File '{DATA_FILE}' not found. Please ensure your Phase 3 corpus CSV is in the directory.")
    st.stop()

def load_data():
    df = pd.read_csv(DATA_FILE)
    # Ensure all required columns exist to prevent KeyError
    required_cols = ['Primary_Reviewer', 'Primary_Decision', 'Exclusion_Reason', 'Exclusion_Notes', 
                     'Verifier_Decision', 'Verifying_Reviewer', 'Final_Decision', 'Final_Rationale', 
                     'JBI_Score', 'JBI_Details']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    return df

df = load_data()

def save_data():
    df.to_csv(DATA_FILE, index=False)

# --- 4. Main UI: The Five Tabs ---
st.title(f"Dashboard: {current_user}")

# Progress Overview
st.markdown("### Your Progress")
assigned_papers = len(df[df['Primary_Reviewer'] == current_user])
completed_primary = len(df[(df['Primary_Reviewer'] == current_user) & (df['Primary_Decision'].notna())])
completed_jbi = len(df[(df['Primary_Reviewer'] == current_user) & (df['JBI_Score'].notna())])

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Papers Assigned", assigned_papers)
with col2:
    primary_pct = int((completed_primary / assigned_papers * 100)) if assigned_papers > 0 else 0
    st.metric("Primary Screening", f"{completed_primary}/{assigned_papers}", f"{primary_pct}%")
with col3:
    jbi_pct = int((completed_jbi / assigned_papers * 100)) if assigned_papers > 0 else 0
    st.metric("JBI Appraisal", f"{completed_jbi}/{assigned_papers}", f"{jbi_pct}%")

# Progress bars
if assigned_papers > 0:
    st.progress(completed_primary / assigned_papers, text=f"Primary Screening: {completed_primary}/{assigned_papers}")
    st.progress(completed_jbi / assigned_papers, text=f"JBI Appraisal: {completed_jbi}/{assigned_papers}")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Primary Screening", 
    "2. Verification Queue", 
    "3. Conflict Resolution",
    "4. JBI Appraisal", 
    "5. PRISMA Metrics"
])

# ==========================================
# TAB 1: PRIMARY SCREENING
# ==========================================
with tab1:
    st.header("Primary Full-Text Screening")
    
    # NEW: Calibration Check
    calibration_papers = df[df['Primary_Reviewer'].isna() | (df['Primary_Reviewer'] == 'All')]
    if len(calibration_papers) > 0:
        st.info("**Calibration Mode Active:** There is a shared calibration paper in the dataset. Please ensure the team appraises this paper together before proceeding with independent screening.")

    pending_primary = df[(df['Primary_Reviewer'] == current_user) & (df['Primary_Decision'].isna())]
    
    if len(pending_primary) == 0:
        st.success("You have no pending primary reviews!")
    else:
        current_idx = pending_primary.index[0]
        row = df.loc[current_idx]
        
        st.subheader(row['Title'])
        st.caption(f"Authors: {row.get('Author', 'Unknown')} | Venue: {row.get('Publication Title', 'Unknown')}")
        
        # Display URL if available with a prominent button
        if pd.notna(row.get('Url')) and str(row.get('Url')).strip():
            st.link_button("Open Full-Text Paper", row['Url'], use_container_width=True, help="Opens the paper in a new tab for review.")
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("INCLUDE (Proceed to JBI Appraisal)", use_container_width=True, type="primary"):
                df.at[current_idx, 'Primary_Decision'] = 'Include'
                df.at[current_idx, 'Final_Decision'] = 'Include'
                save_data()
                st.rerun()
                
        with c2:
            with st.container(border=True):
                st.markdown("**EXCLUDE (Requires Verification)**")
                reason = st.selectbox("PRISMA Exclusion Reason:", EXCLUSION_REASONS, key="exc_reason")
                # NEW: Notes field for rigorous audit trail
                notes = st.text_area("Additional Notes (Briefly explain why it fails):", placeholder="e.g., The study only measures system latency, not user trust...")
                
                if st.button("Submit Exclusion", use_container_width=True):
                    if reason == "Select a reason...":
                        st.error("You must select a primary reason for exclusion.")
                    else:
                        df.at[current_idx, 'Primary_Decision'] = 'Exclude'
                        df.at[current_idx, 'Exclusion_Reason'] = reason
                        df.at[current_idx, 'Exclusion_Notes'] = notes
                        save_data()
                        st.rerun()

# ==========================================
# TAB 2: VERIFICATION QUEUE
# ==========================================
with tab2:
    st.header("Verification Queue")
    pending_verification = df[(df['Primary_Decision'] == 'Exclude') & 
                              (df['Primary_Reviewer'] != current_user) & 
                              (df['Verifier_Decision'].isna())]
    
    if len(pending_verification) == 0:
        st.success("No exclusions pending verification!")
    else:
        v_idx = pending_verification.index[0]
        v_row = df.loc[v_idx]
        
        st.error(f"**Primary Reviewer ({v_row['Primary_Reviewer']}) marked this for EXCLUSION.**")
        st.warning(f"**Stated Reason:** {v_row['Exclusion_Reason']}")
        if pd.notna(v_row['Exclusion_Notes']) and v_row['Exclusion_Notes'].strip():
            st.info(f"**Reviewer Notes:** {v_row['Exclusion_Notes']}")
        
        st.subheader(v_row['Title'])
        
        # Display URL if available
        if pd.notna(v_row.get('Url')) and v_row.get('Url').strip():
            st.markdown(f"[**Access Full-Text**]({v_row['Url']})")
        
        st.markdown("---")
        
        vc1, vc2 = st.columns(2)
        with vc1:
            if st.button("AGREE (Confirm Exclusion)", use_container_width=True):
                df.at[v_idx, 'Verifier_Decision'] = 'Agree (Exclude)'
                df.at[v_idx, 'Final_Decision'] = 'Exclude'
                df.at[v_idx, 'Verifying_Reviewer'] = current_user
                save_data()
                st.rerun()
        with vc2:
            if st.button("DISAGREE (Move to Conflicts)", use_container_width=True, type="primary"):
                df.at[v_idx, 'Verifier_Decision'] = 'Disagree (Conflict)'
                df.at[v_idx, 'Final_Decision'] = 'Conflict'
                df.at[v_idx, 'Verifying_Reviewer'] = current_user
                save_data()
                st.rerun()

# ==========================================
# TAB 3: CONFLICT RESOLUTION (NEW)
# ==========================================
with tab3:
    st.header("Conflict Resolution Panel")
    st.markdown("Papers where the Primary Reviewer and Verifier disagreed.")
    
    conflicts = df[df['Final_Decision'] == 'Conflict']
    
    if len(conflicts) == 0:
        st.success("No active conflicts to resolve. Great team alignment!")
    else:
        c_idx = conflicts.index[0]
        c_row = df.loc[c_idx]
        
        st.subheader(c_row['Title'])
        st.warning(f"**Conflict:** {c_row['Primary_Reviewer']} voted EXCLUDE. {c_row['Verifying_Reviewer']} voted INCLUDE.")
        if pd.notna(c_row['Exclusion_Notes']):
            st.info(f"**Original Exclusion Note:** {c_row['Exclusion_Notes']}")
        
        # Display URL if available
        if pd.notna(c_row.get('Url')) and c_row.get('Url').strip():
            st.markdown(f"[**Access Full-Text**]({c_row['Url']})")
        
        st.markdown("---")
        
        final_rationale = st.text_input("Group Consensus Rationale (Required):", placeholder="e.g., After discussion, we agree the conversational element is too tangential...")
        
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Force INCLUDE", use_container_width=True, type="primary"):
                if not final_rationale:
                    st.error("Please provide a rationale for the final ruling.")
                else:
                    df.at[c_idx, 'Final_Decision'] = 'Include'
                    df.at[c_idx, 'Final_Rationale'] = final_rationale
                    save_data()
                    st.rerun()
        with cc2:
            if st.button("Force EXCLUDE", use_container_width=True):
                if not final_rationale:
                    st.error("Please provide a rationale for the final ruling.")
                else:
                    df.at[c_idx, 'Final_Decision'] = 'Exclude'
                    df.at[c_idx, 'Final_Rationale'] = final_rationale
                    save_data()
                    st.rerun()

# ==========================================
# TAB 4: JBI QUALITY APPRAISAL
# ==========================================
with tab4:
    st.header("JBI Critical Appraisal")
    pending_jbi = df[(df['Final_Decision'] == 'Include') & 
                     (df['Primary_Reviewer'] == current_user) & 
                     (df['JBI_Score'].isna())]
    
    if len(pending_jbi) == 0:
        st.success("No papers pending quality appraisal!")
    else:
        jbi_idx = pending_jbi.index[0]
        jbi_row = df.loc[jbi_idx]
        
        st.subheader(jbi_row['Title'])
        st.markdown("---")
        
        # Display URL if available
        if pd.notna(jbi_row.get('Url')) and jbi_row.get('Url').strip():
            st.markdown(f"[**Access Full-Text**]({jbi_row['Url']})")
        
        st.markdown("---")
        
        q1 = st.radio("1. Was the sample clearly defined and representative?", ("Yes", "No", "Unclear"), horizontal=True)
        q2 = st.radio("2. Were the participants' demographics appropriately detailed?", ("Yes", "No", "Unclear"), horizontal=True)
        q3 = st.radio("3. Was the conversational AI interface clearly described?", ("Yes", "No", "Unclear"), horizontal=True)
        q4 = st.radio("4. Were confounding factors identified?", ("Yes", "No", "Unclear"), horizontal=True)
        q5 = st.radio("5. Were strategies to deal with confounding factors stated?", ("Yes", "No", "Unclear"), horizontal=True)
        q6 = st.radio("6. Were outcomes measured in a valid and reliable way?", ("Yes", "No", "Unclear"), horizontal=True)
        q7 = st.radio("7. Was the statistical/qualitative analysis appropriate?", ("Yes", "No", "Unclear"), horizontal=True)
        q8 = st.radio("8. Are the ethical considerations addressed?", ("Yes", "No", "Unclear"), horizontal=True)
        
        if st.button("Save Quality Score", type="primary"):
            answers = [q1, q2, q3, q4, q5, q6, q7, q8]
            score = answers.count("Yes")
            df.at[jbi_idx, 'JBI_Score'] = f"{score}/8"
            df.at[jbi_idx, 'JBI_Details'] = str(answers)
            save_data()
            st.rerun()

# ==========================================
# TAB 5: PRISMA METRICS (NEW)
# ==========================================
with tab5:
    st.header("PRISMA Flow Diagram Data")
    st.markdown("Use these exact numbers to construct your PRISMA flowchart for the final report.")
    
    total_papers = len(df)
    total_included = len(df[df['Final_Decision'] == 'Include'])
    total_excluded = len(df[df['Final_Decision'] == 'Exclude'])
    total_conflicts = len(df[df['Final_Decision'] == 'Conflict'])
    pending = total_papers - (total_included + total_excluded + total_conflicts)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Full-Texts Assessed", total_papers)
    col2.metric("Pending/In Progress", pending)
    col3.metric("Final Included (Synthesis)", total_included)
    col4.metric("Active Conflicts", total_conflicts)
    
    st.markdown("---")
    
    # Team Progress Overview
    st.subheader("Team Progress Overview")
    team_members = ["Aravind", "Joel", "Chris", "Greg"]
    
    progress_data = []
    for member in team_members:
        member_assigned = len(df[df['Primary_Reviewer'] == member])
        member_completed = len(df[(df['Primary_Reviewer'] == member) & (df['Primary_Decision'].notna())])
        member_jbi = len(df[(df['Primary_Reviewer'] == member) & (df['JBI_Score'].notna())])
        
        if member_assigned > 0:
            completion_rate = int((member_completed / member_assigned) * 100)
            jbi_rate = int((member_jbi / member_assigned) * 100)
        else:
            completion_rate = 0
            jbi_rate = 0
        
        progress_data.append({
            'Reviewer': member,
            'Assigned': member_assigned,
            'Screened': f"{member_completed}/{member_assigned}",
            'Screening %': completion_rate,
            'JBI Done': f"{member_jbi}/{member_assigned}",
            'JBI %': jbi_rate
        })
    
    progress_df = pd.DataFrame(progress_data)
    st.dataframe(progress_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    st.markdown("### Reasons for Exclusion (PRISMA 'Excluded with reasons' box)")
    if total_excluded > 0:
        # Group by reason and count
        exclusion_counts = df[df['Final_Decision'] == 'Exclude']['Exclusion_Reason'].value_counts().reset_index()
        exclusion_counts.columns = ['Reason for Exclusion', 'Count']
        st.dataframe(exclusion_counts, use_container_width=True, hide_index=True)
    else:
        st.info("No papers have been fully excluded yet.")