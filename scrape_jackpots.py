"""
Scrape current jackpot amounts for Jan 8, 2026
"""

import urllib.request
import json
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

def scrape_powerball_jackpot():
    """Scrape PB jackpot from official site."""
    try:
        # Try NY Open Data first
        url = "https://data.ny.gov/api/views/d6yy-54nr/rows.json?accessType=DOWNLOAD"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
        
        # Latest jackpot should be in most recent row
        if data.get('data') and len(data['data']) > 0:
            latest = data['data'][-1]
            # Column index may vary, look for jackpot amount
            for val in latest:
                if isinstance(val, str) and '$' in val and 'M' in val.upper():
                    return val
        
        return None
    except Exception as e:
        print(f"PB jackpot scrape error: {e}")
        return None

def scrape_mm_jackpot():
    """Scrape MM jackpot from official site."""
    try:
        url = "https://www.megamillions.com/"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')
        
        # Look for jackpot pattern
        match = re.search(r'\$(\d+(?:,\d+)*)\s*(?:Million|M)', html, re.IGNORECASE)
        if match:
            return f"${match.group(1)}M"
        
        return None
    except Exception as e:
        print(f"MM jackpot scrape error: {e}")
        return None

def update_jackpots():
    """Update jackpot file with scraped data."""
    jackpot_file = DATA_DIR / "jackpots.json"
    
    # Default jackpots (as of Jan 8, 2026 - will be updated by scraping)
    jackpots = {
        "L4L": {
            "amount": "$7,000/week for life",
            "cashValue": 5750000,
            "nextDraw": "2026-01-08T21:38:00"
        },
        "LA": {
            "amount": "$2.85M",
            "cashValue": 1425000,
            "nextDraw": "2026-01-08T22:00:00"
        },
        "PB": {
            "amount": "$149M",
            "cashValue": 69900000,
            "nextDraw": "2026-01-08T21:59:00"
        },
        "MM": {
            "amount": "$284M",
            "cashValue": 137800000,
            "nextDraw": "2026-01-10T22:00:00"
        },
        "lastUpdated": datetime.now().isoformat()
    }
    
    print("🔍 Scraping current jackpots...")
    
    # Try to scrape real values
    pb_jackpot = scrape_powerball_jackpot()
    if pb_jackpot:
        jackpots["PB"]["amount"] = pb_jackpot
        print(f"✅ PB: {pb_jackpot}")
    else:
        print(f"⏭️  PB: Using default ${jackpots['PB']['amount']}")
    
    mm_jackpot = scrape_mm_jackpot()
    if mm_jackpot:
        jackpots["MM"]["amount"] = mm_jackpot
        print(f"✅ MM: {mm_jackpot}")
    else:
        print(f"⏭️  MM: Using default ${jackpots['MM']['amount']}")
    
    # L4L is always the same
    print(f"ℹ️  L4L: $7K/week (fixed)")
    
    # LA needs manual update (requires JavaScript)
    print(f"ℹ️  LA: ${jackpots['LA']['amount']} (manual)")
    
    # Save
    with open(jackpot_file, 'w') as f:
        json.dump(jackpots, f, indent=2)
    
    print(f"\n💾 Jackpots saved to {jackpot_file}")
    return jackpots

if __name__ == '__main__':
    update_jackpots()
