"""
Fix all data issues:
1. Remove impossible dates (Sunday draws for LA/PB, wrong days for MM)
2. Ensure correct order (newest first)
3. Remove duplicates
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")

def fix_lottery(filename, schedule_days):
    """
    Fix one lottery's data.
    schedule_days: list of valid weekday numbers (0=Mon, 6=Sun)
    """
    file_path = DATA_DIR / filename
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    lottery = data['abbreviation']
    draws = data['draws']
    
    print(f"\n{lottery}:")
    print(f"  Original draws: {len(draws)}")
    
    # Filter out invalid dates
    valid_draws = []
    removed = []
    
    for draw in draws:
        date_obj = datetime.strptime(draw['date'], '%Y-%m-%d')
        
        # Check if day of week is valid
        if schedule_days is None or date_obj.weekday() in schedule_days:
            valid_draws.append(draw)
        else:
            day_name = date_obj.strftime('%A')
            removed.append(f"{draw['date']} ({day_name})")
    
    if removed:
        print(f"  ❌ Removed {len(removed)} impossible dates:")
        for r in removed:
            print(f"     {r}")
    
    # Remove duplicates (by date)
    seen_dates = set()
    unique_draws = []
    dupes = 0
    
    for draw in valid_draws:
        if draw['date'] not in seen_dates:
            seen_dates.add(draw['date'])
            unique_draws.append(draw)
        else:
            dupes += 1
    
    if dupes > 0:
        print(f"  🔧 Removed {dupes} duplicates")
    
    # Sort by date (newest first)
    unique_draws.sort(key=lambda x: x['date'], reverse=True)
    
    # Update data
    data['draws'] = unique_draws
    data['lastUpdated'] = datetime.now().isoformat()
    
    # Save
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  ✅ Fixed: {len(unique_draws)} valid draws")
    print(f"  Latest: {unique_draws[0]['date']}")

print("=" * 70)
print("FIXING ALL LOTTERY DATA")
print("=" * 70)

# L4L: Daily (all days valid)
fix_lottery('l4l.json', None)

# LA: Mon/Wed/Sat only
fix_lottery('la.json', [0, 2, 5])

# PB: Mon/Wed/Sat only
fix_lottery('pb.json', [0, 2, 5])

# MM: Tue/Fri only
fix_lottery('mm.json', [1, 4])

print("\n" + "=" * 70)
print("✅ ALL DATA FIXED")
print("=" * 70)
