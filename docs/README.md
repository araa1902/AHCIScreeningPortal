# AHCI Screening Portal

A systematic review screening tool for HCI research papers with an interactive screening interface and conflict analysis.

## 📁 Project Structure

```
Advanced HCI Script/
├── src/                          # Main source code
│   ├── screeningPortal.py        # Screening interface
│   ├── mergeAudit.py             # Audit trail generator
│   ├── syncAuditToZotero.py      # Zotero sync tool
│   ├── p3_portal.py              # P3 portal utilities
│   ├── utils/                    # Utility scripts
│   │   └── build_p3CSV.py        # P3 CSV builder
│   ├── tests/                    # Test files
│   │   └── test_zotero.py        # Zotero sync tests
│   └── logs/                     # Application logs
├── data/                         # Data files
│   ├── input/                    # Input data
│   ├── screening/                # Screening results
│   └── audit/                    # Final audit files
├── docs/                         # Documentation
├── config/                       # Configuration & requirements
├── backups/                      # Backup files
└── README.md                     # This file
```

## Team

- **Member A: Aravind** (Pool 1 - `data/screening/Pool_1_Reviewer_A.csv`)
- **Member B: Joel** (Pool 1 - `data/screening/Pool_1_Reviewer_B.csv`)
- **Member C: Chris** (Pool 2 - `data/screening/Pool_2_Reviewer_C.csv`)
- **Member D: Greg** (Pool 2 - `data/screening/Pool_2_Reviewer_D.csv`)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r config/requirements.txt
```

### 2. Run the Screening Portal

```bash
streamlit run src/screeningPortal.py
```

### 3. Generate Audit Trail (After Screening Complete)

```bash
python src/mergeAudit.py
```

### 4. Sync to Zotero (After Conflict Resolution)

```bash
python src/syncAuditToZotero.py
```

## How to Use

### Phase 1: Screening

1. **Select your name** from the sidebar dropdown
2. **Review the paper** - title, authors, abstract
3. **Make a decision** - Include, For Consideration, or Exclude
4. **Next paper** automatically loads when you decide
5. **Repeat** until all papers are screened

Decisions save automatically to your CSV file in `data/screening/`.

### Phase 2: Conflict Resolution

1. Run `python src/mergeAudit.py` to generate conflict reports
2. Open `data/audit/Conflict_Resolution_Log.csv` to review conflicts
3. Make final decisions for disputed papers
4. Run `mergeAudit.py` again to regenerate the audit trail

### Phase 3: Zotero Sync

1. Set up `.zotero_config.json` in the `config/` folder (see `docs/ZOTERO_SETUP.md`)
2. Create "Inclusion" and "Exclusion" collections in Zotero
3. Run `python src/syncAuditToZotero.py` to organize papers

## Output Files

### `data/screening/`

- Individual reviewer CSV files for each pool
- `Screening_Log.csv` - PRISMA Stage 2 metrics
- `Screening_Log.json` - Structured screening metadata

### `data/audit/`

- `Conflict_Resolution_Log.csv` - Disputed papers awaiting final decisions
- `Audit_Trail.csv` - Complete screening record (PRISMA compliance)

## Requirements

- Python 3.7+
- pandas
- scikit-learn
- streamlit
- pyzotero (for Zotero sync)

See `config/requirements.txt` for full list.
