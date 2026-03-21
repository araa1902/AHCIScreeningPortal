# AHCI Screening Portal

A systematic review screening tool for HCI research papers with an interactive screening interface and conflict analysis.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Screening Portal

```bash
streamlit run screeningPortal.py
```

Opens at `http://localhost:8501`

## How to Use

1. **Select your name** from the sidebar dropdown
2. **Review the paper** - title, authors, abstract
3. **Make a decision** - Include, For Consideration, or Exclude
4. **Next paper** automatically loads when you decide
5. **Repeat** until all papers are screened

Decisions save automatically to your CSV file.

## Files

- `screeningPortal.py` - Screening interface
- `mergeAudit.py` - Conflict analysis
- `Pool_1_Reviewer_A.csv` - Aravind's papers
- `Pool_1_Reviewer_B.csv` - Joel's papers
- `Pool_2_Reviewer_C.csv` - Chris's papers
- `Pool_2_Reviewer_D.csv` - Greg's papers

## Requirements

- Python 3.7+
- pandas
- scikit-learn
- streamlit

All installed with: `pip install -r requirements.txt`
