"""
Verify all drawings are in correct chronological order
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")

def verify_order(filename):
    """Check if draws are in correct order (newest first)."""
    file_path = DATA_DIR / filename
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    lottery = data['abbreviation']
    draws = data['draws']
    
    print(f"\n{lottery}:")
    print(f"  Total draws: {len(draws)}")
    
    # Check order
    dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in draws]
    
    is_newest_first = all(dates[i] >= dates[i+1] for i in range(len(dates)-1))
    is_oldest_first = all(dates[i] <= dates[i+1] for i in range(len(dates)-1))
    
    if is_newest_first:
        print(f"  ✅ Order: NEWEST FIRST (correct)")
    elif is_oldest_first:
        print(f"  ❌ Order: OLDEST FIRST (needs reversal)")
    else:
        print(f"  ❌ Order: MIXED/RANDOM (needs sorting)")
    
    print(f"  First in array: {draws[0]['date']}")
    print(f"  Last in array: {draws[-1]['date']}")
    
    return is_newest_first

print("=" * 60)
print("VERIFYING DRAWING ORDER")
print("=" * 60)

all_correct = True
all_correct &= verify_order('l4l.json')
all_correct &= verify_order('la.json')
all_correct &= verify_order('pb.json')
all_correct &= verify_order('mm.json')

print("\n" + "=" * 60)
if all_correct:
    print("✅ ALL LOTTERIES IN CORRECT ORDER")
else:
    print("⚠️ SOME LOTTERIES NEED REORDERING")
print("=" * 60)
