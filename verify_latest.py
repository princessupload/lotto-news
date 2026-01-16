"""
Verify latest draws for all 4 lotteries and check for impossible dates
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")

def check_lottery(filename, schedule):
    """Check one lottery's latest draws."""
    file_path = DATA_DIR / filename
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    lottery = data['abbreviation']
    draws = data['draws']
    
    print(f"\n{lottery} ({data['lottery']}):")
    print(f"  Schedule: {schedule}")
    print(f"  Total draws: {len(draws)}")
    print(f"\n  Last 5 draws:")
    
    for draw in draws[:5]:
        date_str = draw['date']
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = date_obj.strftime('%A')
        
        # Check if date is valid for schedule
        valid = True
        if schedule == 'Mon/Wed/Sat' and date_obj.weekday() not in [0, 2, 5]:
            valid = False
        elif schedule == 'Tue/Fri' and date_obj.weekday() not in [1, 4]:
            valid = False
        
        status = "✓" if valid else "❌ IMPOSSIBLE"
        print(f"    {status} {date_str} ({day_name}): {draw['main']} + {draw['bonus']}")

print("=" * 70)
print("VERIFYING LATEST DRAWS - JAN 8, 2026")
print("=" * 70)

check_lottery('l4l.json', 'Daily')
check_lottery('la.json', 'Mon/Wed/Sat')
check_lottery('pb.json', 'Mon/Wed/Sat')
check_lottery('mm.json', 'Tue/Fri')

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
