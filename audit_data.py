"""
Complete data audit for all 4 lotteries
Verify: date ranges, order, completeness, DDS compliance
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")

# DDS start dates (Digital Drawing System)
DDS_DATES = {
    'L4L': '2023-02-27',  # Lucky for Life DDS start
    'LA': '2023-04-17',   # Lotto America DDS start (confirmed)
    'PB': '2020-01-01',   # Powerball (estimate - need to verify)
    'MM': '2020-01-01'    # Mega Millions (estimate - need to verify)
}

def audit_file(lottery_key, filename):
    """Audit one lottery's data file."""
    print(f"\n{'='*60}")
    print(f"AUDITING {lottery_key}")
    print(f"{'='*60}")
    
    file_path = DATA_DIR / filename
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            draws = data.get('draws', [])
        if not draws:
            print("❌ No draws found!")
            return None
        total = len(draws)
        
        # Get date range
        dates = [d['date'] for d in draws if 'date' in d]
        if not dates:
            print(f"❌ No dates found in draws!")
            return None
        
        first_date = min(dates)
        last_date = max(dates)
        dds_start = DDS_DATES.get(lottery_key, 'Unknown')
        
        print(f"📊 Total Draws: {total}")
        print(f"📅 Date Range: {first_date} → {last_date}")
        print(f"🎯 DDS Start: {dds_start}")
        
        # Check if we have DDS-era data
        if first_date <= dds_start:
            print(f"✅ Has DDS-era data (starts at or before {dds_start})")
        else:
            print(f"⚠️  Missing early DDS data (should start at {dds_start}, actually starts {first_date})")
        
        # Check order
        ordered_dates = sorted(dates)
        if dates == ordered_dates:
            print(f"✅ Dates are in chronological order (oldest first)")
        elif dates == list(reversed(ordered_dates)):
            print(f"⚠️  Dates are in reverse order (newest first)")
        else:
            print(f"❌ Dates are not properly ordered!")
        
        # Check for duplicates
        if len(dates) != len(set(dates)):
            dupes = len(dates) - len(set(dates))
            print(f"⚠️  {dupes} duplicate dates found!")
        else:
            print(f"✅ No duplicate dates")
        
        # Check for gaps (skip if daily lottery)
        if lottery_key != 'L4L':
            print(f"ℹ️  Gap analysis skipped (not daily lottery)")
        
        # Sample first and last draw
        print(f"\n📍 First Draw ({first_date}):")
        first_draw = next(d for d in draws if d.get('date') == first_date)
        print(f"   Numbers: {first_draw.get('main', [])} + {first_draw.get('bonus', '?')}")
        
        print(f"\n📍 Last Draw ({last_date}):")
        last_draw = next(d for d in draws if d.get('date') == last_date)
        print(f"   Numbers: {last_draw.get('main', [])} + {last_draw.get('bonus', '?')}")
        
        return {
            'lottery': lottery_key,
            'total': total,
            'first_date': first_date,
            'last_date': last_date,
            'dds_start': dds_start,
            'ordered': dates == ordered_dates or dates == list(reversed(ordered_dates)),
            'has_dds_data': first_date <= dds_start
        }
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("=" * 60)
    print("COMPLETE DATA AUDIT - ALL 4 LOTTERIES")
    print(f"Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    
    # Audit all 4 (new data files)
    results.append(audit_file('L4L', 'l4l.json'))
    results.append(audit_file('LA', 'la.json'))
    results.append(audit_file('PB', 'pb.json'))
    results.append(audit_file('MM', 'mm.json'))
    
    # Summary
    print(f"\n{'='*60}")
    print("AUDIT SUMMARY")
    print(f"{'='*60}")
    
    for r in results:
        if r:
            status = "✅" if r['ordered'] and r['has_dds_data'] else "⚠️"
            print(f"{status} {r['lottery']}: {r['total']} draws ({r['first_date']} → {r['last_date']})")
    
    print(f"\n{'='*60}")
    print("✅ Audit Complete")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
