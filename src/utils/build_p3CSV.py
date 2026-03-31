import pandas as pd
import numpy as np
import os

print("Building Phase 3 Tracker...")

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Load the Phase 2 Audit Trail
audit_file = os.path.join(project_root, "data", "audit", "Audit_Trail.csv")
df_audit = pd.read_csv(audit_file)

# 1b. Load the original input file to extract URLs
input_file = os.path.join(project_root, "data", "input", "Pre-Screening Papers - Papers with Abstract to Screen.csv")
df_input = pd.read_csv(input_file)

# 2. Filter ONLY for papers that passed Phase 2
df_included = df_audit[df_audit['Final_Decision'] == 'Include'].copy()

# 2b. Merge with input file to get URLs (matching on Title)
df_included = df_included.merge(
    df_input[['Title', 'Url']],
    on='Title',
    how='left'
)

# 3. Isolate the metadata
phase3_df = df_included[['Title', 'Author', 'Publication Title', 'Url']].copy()

# Note: Since Publication Year isn't in the Audit Trail, we add a placeholder.
# You can easily paste the years in from your original Scopus/Zotero export later.
phase3_df['Publication Year'] = "Unknown" 

# 4. Add the blank Phase 3 tracking columns required by the portal
blank_cols = [
    'Primary_Decision', 'Exclusion_Reason', 'Exclusion_Notes',
    'Verifier_Decision', 'Verifying_Reviewer', 'Final_Decision',
    'Final_Rationale', 'JBI_Score', 'JBI_Details'
]
for col in blank_cols:
    phase3_df[col] = None

# 5. Shuffle and assign Reviewers evenly
team = ['Aravind', 'Joel', 'Chris', 'Greg']
phase3_df = phase3_df.sample(frac=1, random_state=42).reset_index(drop=True)

# Distribute papers round-robin style
phase3_df['Primary_Reviewer'] = [team[i % len(team)] for i in range(len(phase3_df))]

# 6. Set up the Calibration Paper (Crucial for the 80+ methodology)
phase3_df.at[0, 'Primary_Reviewer'] = 'All'

# 7. Reorder columns to match the Phase 3 portal exactly
cols = ['Title', 'Author', 'Publication Title', 'Publication Year', 'Url', 'Primary_Reviewer'] + blank_cols
phase3_df = phase3_df[cols]

# 8. Export the final file
output_file = os.path.join(project_root, "data", "screening", "Phase3_Tracker.csv")
phase3_df.to_csv(output_file, index=False)
print(f"Success! Created 'Phase3_Tracker.csv' with {len(phase3_df)} papers ready for Full-Text Screening.")
print(f"File saved to: {output_file}")
print(f"Paper 1 has been set to 'All' for your calibration exercise.")