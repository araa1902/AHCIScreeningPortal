"""
Sync Audit Trail Decisions to Zotero
=====================================
Reads the Audit_Trail.csv and automatically organizes papers in Zotero
based on final decisions (Include/Exclude).

Prerequisites:
1. Install pyzotero: pip install pyzotero
2. Get your Zotero API key from https://www.zotero.org/settings/keys
3. Create a .zotero_config.json file with your credentials

Usage:
    python syncAuditToZotero.py
"""

import pandas as pd
import json
import os
import sys
import time
import logging
import re
from datetime import datetime

try:
    from pyzotero import zotero
except ImportError:
    print("pyzotero not installed. Install it with: pip install pyzotero")
    sys.exit(1)


# --------------------------------------------------
# Configuration
# --------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(SCRIPT_DIR) # Assuming script is in a subfolder. Change to SCRIPT_DIR if in root.

CONFIG_FILE = os.path.join(WORKSPACE_ROOT, "config", ".zotero_config.json")
# Fallback to local script directory if workspace config doesn't exist
if not os.path.exists(CONFIG_FILE):
    CONFIG_FILE = os.path.join(SCRIPT_DIR, ".zotero_config.json")

AUDIT_FILE = os.path.join(SCRIPT_DIR, "Audit_Trail.csv")
ZOTERO_COLLECTIONS = {
    "Inclusion": None,
    "Exclusion": None,
}

BATCH_SIZE = 50 
API_DELAY = 0.1  
LOG_FILE = os.path.join(SCRIPT_DIR, "sync_log.txt")

_ZOTERO_ITEMS_CACHE = None
_ZOTERO_ITEMS_CACHE_LOADED = False

# --------------------------------------------------
# Logging Setup
# --------------------------------------------------
def setup_logging():
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logger = logging.getLogger('ZoteroSync')
    logger.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
def clean_text(text):
    """Normalize text by stripping punctuation, spaces, and converting to lowercase for robust matching."""
    if not isinstance(text, str):
        return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def load_config():
    """Load Zotero credentials from config file."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Config file '{CONFIG_FILE}' not found.")
        sys.exit(1)
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Invalid JSON in {CONFIG_FILE}")
        sys.exit(1)

def load_audit_trail():
    """Load the Audit_Trail.csv"""
    if not os.path.exists(AUDIT_FILE):
        print(f"{AUDIT_FILE} not found. Please ensure it is in the same directory.")
        sys.exit(1)
    
    try:
        return pd.read_csv(AUDIT_FILE)
    except Exception as e:
        print(f"Error reading {AUDIT_FILE}: {e}")
        sys.exit(1)

def init_zotero(config):
    """Initialize Zotero API connection."""
    # Handle user_id vs group_id naming robustly
    library_id = config.get('group_id') or config.get('user_id') or config.get('library_id')
    api_key = config.get('api_key')
    library_type = config.get('library_type', 'user')

    try:
        z = zotero.Zotero(library_id, library_type, api_key)
        # Verify connection
        z.key_info()
        return z
    except Exception as e:
        print(f"Failed to connect to Zotero: {e}")
        sys.exit(1)

def find_collections(z):
    """Find Inclusion and Exclusion collection keys using pagination to ensure all are searched."""
    try:
        # Fetch ALL collections, not just the top 50
        collections = []
        start = 0
        limit = 50
        while True:
            batch = z.collections(limit=limit, start=start)
            if not batch: break
            collections.extend(batch)
            if len(batch) < limit: break
            start += limit

        collection_map = {col['data']['name']: col['key'] for col in collections}
        
        missing = [name for name in ZOTERO_COLLECTIONS.keys() if name not in collection_map]
        
        if missing:
            print(f"Missing collections in Zotero: {', '.join(missing)}. Please create them first.")
            sys.exit(1)
            
        for name in ZOTERO_COLLECTIONS.keys():
            ZOTERO_COLLECTIONS[name] = collection_map[name]
        
        print("Found collections:")
        for name, key in ZOTERO_COLLECTIONS.items():
            print(f"   - {name}: {key}")
        
        return True
    except Exception as e:
        print(f"Error fetching collections: {e}")
        sys.exit(1)

def load_all_zotero_items(z):
    """Load all items from Zotero library in batches."""
    global _ZOTERO_ITEMS_CACHE, _ZOTERO_ITEMS_CACHE_LOADED
    
    if _ZOTERO_ITEMS_CACHE_LOADED:
        return _ZOTERO_ITEMS_CACHE
    
    try:
        print("Loading all items from Zotero (this may take a moment)...")
        all_items = []
        start = 0
        limit = 100 
        
        while True:
            batch = z.items(limit=limit, start=start)
            if not batch: break
            
            all_items.extend(batch)
            print(f"  Loaded {len(all_items)} items...")
            
            if len(batch) < limit: break
            start += limit
            time.sleep(API_DELAY)
        
        _ZOTERO_ITEMS_CACHE = all_items
        _ZOTERO_ITEMS_CACHE_LOADED = True
        logger.info(f"Loaded {len(all_items)} total items from Zotero")
        return all_items
    except Exception as e:
        logger.error(f"Error loading Zotero items: {e}")
        return []

def search_paper_in_zotero(title, all_items):
    """Search for a paper purely in the local cache using normalized alphanumeric strings."""
    try:
        normalized_target = clean_text(title)
        if not normalized_target:
            return None

        for item in all_items:
            item_data = item.get('data', {})
            item_type = item_data.get('itemType', '')
            
            # Skip attachments and notes
            if item_type in ['note', 'attachment']:
                continue
            
            item_title = item_data.get('title', '')
            normalized_item_title = clean_text(item_title)

            # Look for exact normalized match (ignores punctuation and spaces)
            if normalized_target == normalized_item_title:
                return item
            
            # Fallback for substrings if title is reasonably long
            if len(normalized_target) > 20 and (normalized_target in normalized_item_title or normalized_item_title in normalized_target):
                return item
                
        return None
    except Exception as e:
        logger.error(f"Unexpected error searching for '{title}': {e}")
        return None

def add_paper_to_collection(z, item, collection_key):
    """Add a paper to a collection safely."""
    try:
        item_key = item['key']
        time.sleep(API_DELAY)
        
        # Initialize collections field if missing
        if 'collections' not in item['data']:
            item['data']['collections'] = []
        
        # Check if already in collection
        if collection_key in item['data']['collections']:
            return None # Already added
        
        # Add and update
        item['data']['collections'].append(collection_key)
        
        z.update_item(item)
        return True
            
    except Exception as e:
        logger.error(f"Zotero API error updating item {item.get('key')}: {str(e)}")
        return False

def sync_audit_to_zotero(audit_df, z):
    """Sync audit trail decisions to Zotero with batch processing."""
    print("\n" + "="*60 + "\nSYNCING AUDIT TRAIL TO ZOTERO\n" + "="*60)
    
    # Filter for valid Include/Exclude decisions
    decided_papers = audit_df[audit_df['Final_Decision'].isin(['Include', 'Exclude'])].copy()
    
    if decided_papers.empty:
        print("WARNING: No papers with 'Include' or 'Exclude' decisions found in Audit_Trail.csv")
        return
    
    print(f"\nTotal papers to sync: {len(decided_papers)}")
    
    results = {'found': 0, 'added_to_inclusion': 0, 'added_to_exclusion': 0, 'already_in': 0, 'not_found': 0, 'errors': 0}
    failed_papers = []
    
    # Load all items into memory once
    all_zotero_items = load_all_zotero_items(z)
    
    for batch_idx, (idx, row) in enumerate(decided_papers.iterrows()):
        title = row.get('Title', '')
        decision = row.get('Final_Decision')
        
        target_col_key = ZOTERO_COLLECTIONS['Inclusion'] if decision == 'Include' else ZOTERO_COLLECTIONS['Exclusion']
        
        item = search_paper_in_zotero(title, all_zotero_items)
        
        if item:
            results['found'] += 1
            result = add_paper_to_collection(z, item, target_col_key)
            
            if result is True:
                if decision == 'Include': results['added_to_inclusion'] += 1
                else: results['added_to_exclusion'] += 1
                print(f"  Added to {decision}: {title[:60]}...")
            elif result is None:
                results['already_in'] += 1
                print(f"  Already in {decision}: {title[:60]}...")
            else:
                results['errors'] += 1
                failed_papers.append((title, decision, 'API Update Failed'))
                print(f"  Error updating: {title[:60]}...")
        else:
            results['not_found'] += 1
            failed_papers.append((title, decision, 'Not found in Zotero'))
            print(f"  Not found: {title[:60]}...")
        
        if (batch_idx + 1) % BATCH_SIZE == 0:
            time.sleep(1) # Extra buffer for rate limits

    # Print Summary
    print("\n" + "="*60 + "\nSYNC SUMMARY\n" + "="*60)
    print(f"Papers synced: {results['added_to_inclusion'] + results['added_to_exclusion']} (Included: {results['added_to_inclusion']}, Excluded: {results['added_to_exclusion']})")
    print(f"Already mapped: {results['already_in']}")
    print(f"Missing in Zotero: {results['not_found']}")
    print(f"Errors: {results['errors']}\n" + "="*60)

    if failed_papers:
        print("\nMISSING/FAILED PAPERS REPORT saved to log.")
        for title, col, reason in failed_papers:
            logger.error(f"Failed: {title} | Target: {col} | Reason: {reason}")
            
# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    print("Zotero Audit Trail Sync Tool Started")
    try:
        config = load_config()
        audit_df = load_audit_trail()
        
        z = init_zotero(config)
        print("Connected to Zotero Group Library")
        
        find_collections(z)
        sync_audit_to_zotero(audit_df, z)
        
        print("\nSync complete! Check your Zotero Library.")
    except Exception as e:
        logger.exception("Fatal Error")
        print(f"\nFatal error: {e}")

if __name__ == "__main__":
    main()