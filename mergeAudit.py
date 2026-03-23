import pandas as pd
from sklearn.metrics import cohen_kappa_score
import json
import warnings
warnings.filterwarnings('ignore') # Suppress pandas merge warnings

print("📚 Initiating Systematic Review Audit Phase...")

# --- 1. Load the Completed Datasets ---
# Pool 1
df_A = pd.read_csv("Pool_1_Reviewer_A.csv")
df_B = pd.read_csv("Pool_1_Reviewer_B.csv")
# Pool 2
df_C = pd.read_csv("Pool_2_Reviewer_C.csv")
df_D = pd.read_csv("Pool_2_Reviewer_D.csv")

# --- 2. Merge Pools for Comparison ---
# Merging on Title ensures we align the exact same papers
# Select only fields that exist in the CSVs
pool_1 = pd.merge(df_A[['Title', 'Author', 'Publication Title', 'Reviewer_Decision']], 
                  df_B[['Title', 'Reviewer_Decision']], 
                  on='Title', suffixes=('_A', '_B'), how='inner')

pool_2 = pd.merge(df_C[['Title', 'Author', 'Publication Title', 'Reviewer_Decision']], 
                  df_D[['Title', 'Reviewer_Decision']], 
                  on='Title', suffixes=('_C', '_D'), how='inner')

# --- 3. Calculate Inter-Rater Reliability (Cohen's Kappa) ---
# Filter out "Pending" just in case someone missed a paper
p1_clean = pool_1[(pool_1['Reviewer_Decision_A'] != 'Pending') & (pool_1['Reviewer_Decision_B'] != 'Pending')]
p2_clean = pool_2[(pool_2['Reviewer_Decision_C'] != 'Pending') & (pool_2['Reviewer_Decision_D'] != 'Pending')]

kappa_1 = cohen_kappa_score(p1_clean['Reviewer_Decision_A'], p1_clean['Reviewer_Decision_B'])
kappa_2 = cohen_kappa_score(p2_clean['Reviewer_Decision_C'], p2_clean['Reviewer_Decision_D'])

# --- 4. Tally Initial Decisions ---
def calculate_tallies(df, rev1_col, rev2_col):
    both_include = len(df[(df[rev1_col] == 'Include') & (df[rev2_col] == 'Include')])
    both_exclude = len(df[(df[rev1_col] == 'Exclude') & (df[rev2_col] == 'Exclude')])
    conflicts = len(df[df[rev1_col] != df[rev2_col]])
    considerations = len(df[(df[rev1_col] == 'For Consideration') | (df[rev2_col] == 'For Consideration')])
    return both_include, both_exclude, conflicts, considerations

p1_stats = calculate_tallies(pool_1, 'Reviewer_Decision_A', 'Reviewer_Decision_B')
p2_stats = calculate_tallies(pool_2, 'Reviewer_Decision_C', 'Reviewer_Decision_D')

# --- 5. Generate THE SCREENING LOG (Console Output for Report) ---
print("\n" + "="*50)
print("📊 THE SCREENING LOG (PRISMA STAGE 2)")
print("="*50)
print(f"Total Papers Screened: {len(pool_1) + len(pool_2)}")
print(f"\n--- POOL 1 (Aravind & Joel) ---")
print(f"Raw Assigned: {len(pool_1)}")
print(f"Both Include: {p1_stats[0]} | Both Exclude: {p1_stats[1]}")
print(f"Absolute Conflicts (Disagreements): {p1_stats[2]}")
print(f"Cohen's Kappa (IRR): {kappa_1:.3f}")

print(f"\n--- POOL 2 (Chris & Greg) ---")
print(f"Raw Assigned: {len(pool_2)}")
print(f"Both Include: {p2_stats[0]} | Both Exclude: {p2_stats[1]}")
print(f"Absolute Conflicts (Disagreements): {p2_stats[2]}")
print(f"Cohen's Kappa (IRR): {kappa_2:.3f}")
print("="*50)

# --- 5b. Save THE SCREENING LOG to CSV and JSON ---
screening_log_data = {
    "Metric": [
        "Total Papers Screened",
        "Pool 1 - Raw Assigned",
        "Pool 1 - Both Include",
        "Pool 1 - Both Exclude",
        "Pool 1 - Conflicts (Disagreements)",
        "Pool 1 - Cohen's Kappa (IRR)",
        "Pool 2 - Raw Assigned",
        "Pool 2 - Both Include",
        "Pool 2 - Both Exclude",
        "Pool 2 - Conflicts (Disagreements)",
        "Pool 2 - Cohen's Kappa (IRR)",
    ],
    "Value": [
        len(pool_1) + len(pool_2),
        len(pool_1),
        p1_stats[0],
        p1_stats[1],
        p1_stats[2],
        f"{kappa_1:.3f}",
        len(pool_2),
        p2_stats[0],
        p2_stats[1],
        p2_stats[2],
        f"{kappa_2:.3f}",
    ]
}

screening_log_df = pd.DataFrame(screening_log_data)
screening_log_df.to_csv("Screening_Log.csv", index=False)

# Also save as JSON for structured metadata
import json
screening_log_json = {
    "title": "The Screening Log (PRISMA Stage 2)",
    "total_papers_screened": len(pool_1) + len(pool_2),
    "pool_1": {
        "reviewers": ["Aravind (Member A)", "Joel (Member B)"],
        "raw_assigned": len(pool_1),
        "both_include": int(p1_stats[0]),
        "both_exclude": int(p1_stats[1]),
        "conflicts_disagreements": int(p1_stats[2]),
        "cohens_kappa_irr": float(f"{kappa_1:.3f}"),
    },
    "pool_2": {
        "reviewers": ["Chris (Member C)", "Greg (Member D)"],
        "raw_assigned": len(pool_2),
        "both_include": int(p2_stats[0]),
        "both_exclude": int(p2_stats[1]),
        "conflicts_disagreements": int(p2_stats[2]),
        "cohens_kappa_irr": float(f"{kappa_2:.3f}"),
    }
}

with open("Screening_Log.json", "w") as f:
    json.dump(screening_log_json, f, indent=2)

print(f"\n✅ Created 'Screening_Log.csv' and 'Screening_Log.json' with all PRISMA Stage 2 metrics.")

# --- 6. Generate THE CONFLICT RESOLUTION LOG (CSV Output) ---
# Isolate all rows where raters disagreed OR someone voted "For Consideration"
conflicts_1 = pool_1[(pool_1['Reviewer_Decision_A'] != pool_1['Reviewer_Decision_B']) | 
                     (pool_1['Reviewer_Decision_A'] == 'For Consideration') | 
                     (pool_1['Reviewer_Decision_B'] == 'For Consideration')].copy()

conflicts_2 = pool_2[(pool_2['Reviewer_Decision_C'] != pool_2['Reviewer_Decision_D']) | 
                     (pool_2['Reviewer_Decision_C'] == 'For Consideration') | 
                     (pool_2['Reviewer_Decision_D'] == 'For Consideration')].copy()

# Standardize columns for the final output
conflicts_1.rename(columns={'Reviewer_Decision_A': 'Vote_1', 'Reviewer_Decision_B': 'Vote_2'}, inplace=True)
conflicts_2.rename(columns={'Reviewer_Decision_C': 'Vote_1', 'Reviewer_Decision_D': 'Vote_2'}, inplace=True)

conflicts_1['Pool'] = 'Pool 1 (A&B)'
conflicts_2['Pool'] = 'Pool 2 (C&D)'

all_conflicts = pd.concat([conflicts_1, conflicts_2], ignore_index=True)

# Add the blank columns required by your methodology
all_conflicts['Final Ruling (Include/Exclude)'] = ""
all_conflicts['Rationale (One Sentence)'] = ""

# Reorder columns for better readability
output_columns = ['Pool', 'Title', 'Author', 'Publication Title', 'Vote_1', 'Vote_2', 'Final Ruling (Include/Exclude)', 'Rationale (One Sentence)']
all_conflicts = all_conflicts[output_columns]

# Save to CSV
all_conflicts.to_csv("Conflict_Resolution_Log.csv", index=False)
print(f"\n✅ Created 'Conflict_Resolution_Log.csv' with {len(all_conflicts)} disputed papers ready for arbitration.")

# --- 7. Generate THE AUDIT TRAIL (Complete Screening Record) ---
print("\n" + "="*50)
print("📋 GENERATING AUDIT TRAIL")
print("="*50)

audit_trail = []

# Process Pool 1
for _, row in pool_1.iterrows():
    entry = {
        'Pool': 'Pool 1 (Aravind & Joel)',
        'Title': row['Title'],
        'Author': row['Author'],
        'Publication Title': row['Publication Title'],
        'Vote_Reviewer_1': row['Reviewer_Decision_A'],
        'Vote_Reviewer_2': row['Reviewer_Decision_B'],
        'Agreement': 'Yes' if row['Reviewer_Decision_A'] == row['Reviewer_Decision_B'] else 'No',
        'Final_Decision': None,
        'Rationale': None,
        'Status': 'Agreed' if row['Reviewer_Decision_A'] == row['Reviewer_Decision_B'] else 'Needs Resolution'
    }
    audit_trail.append(entry)

# Process Pool 2
for _, row in pool_2.iterrows():
    entry = {
        'Pool': 'Pool 2 (Chris & Greg)',
        'Title': row['Title'],
        'Author': row['Author'],
        'Publication Title': row['Publication Title'],
        'Vote_Reviewer_1': row['Reviewer_Decision_C'],
        'Vote_Reviewer_2': row['Reviewer_Decision_D'],
        'Agreement': 'Yes' if row['Reviewer_Decision_C'] == row['Reviewer_Decision_D'] else 'No',
        'Final_Decision': None,
        'Rationale': None,
        'Status': 'Agreed' if row['Reviewer_Decision_C'] == row['Reviewer_Decision_D'] else 'Needs Resolution'
    }
    audit_trail.append(entry)

# Convert to DataFrame
audit_df = pd.DataFrame(audit_trail)

# Load and merge conflict resolution data if it exists
import os
if os.path.exists("Conflict_Resolution_Log.csv"):
    res_df = pd.read_csv("Conflict_Resolution_Log.csv")
    
    # Update audit trail with final decisions and rationales
    for _, res_row in res_df.iterrows():
        mask = audit_df['Title'] == res_row['Title']
        if mask.any():
            idx = audit_df.index[mask].tolist()[0]
            # Map the old column names to new ones
            final_decision = res_row.get('Final Ruling (Include/Exclude)', res_row.get('Final_Decision'))
            rationale = res_row.get('Rationale (One Sentence)', res_row.get('Rationale'))
            
            audit_df.at[idx, 'Final_Decision'] = final_decision
            audit_df.at[idx, 'Rationale'] = rationale
            audit_df.at[idx, 'Status'] = 'Resolved'
    
    # For agreed papers, use the agreed decision as final
    mask_agreed = audit_df['Status'] == 'Agreed'
    audit_df.loc[mask_agreed, 'Final_Decision'] = audit_df.loc[mask_agreed, 'Vote_Reviewer_1']

# Reorder columns for better readability
output_columns = [
    'Pool', 'Title', 'Author', 'Publication Title',
    'Vote_Reviewer_1', 'Vote_Reviewer_2', 'Agreement',
    'Final_Decision', 'Rationale', 'Status'
]
audit_df = audit_df[output_columns]

# Save to CSV
audit_df.to_csv("Audit_Trail.csv", index=False)
print(f"\n✅ Created 'Audit_Trail.csv' with complete screening history:")
print(f"   - Total papers: {len(audit_df)}")
print(f"   - Agreed decisions: {len(audit_df[audit_df['Status'] == 'Agreed'])}")
print(f"   - Needing resolution: {len(audit_df[audit_df['Status'] == 'Needs Resolution'])}")
print(f"   - Already resolved: {len(audit_df[audit_df['Status'] == 'Resolved'])}")
print("="*50)