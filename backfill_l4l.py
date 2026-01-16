"""
Backfill L4L data from backup file with complete history since Feb 27, 2023
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

BACKUP_FILE = Path(__file__).parent.parent / 'LOTTERY_PROJECT_BACKUP_2025-12-07_183040' / 'L4L_DATA' / 'LUCKY drawing in order of balls called SINCE FEBRUARY 27 2023.txt'
OUTPUT_FILE = Path(__file__).parent / 'data' / 'l4l.json'

def parse_backup():
    """Parse the backup file and generate draws with dates."""
    with open(BACKUP_FILE, 'r') as f:
        lines = f.readlines()
    
    # Skip header lines (first 5 lines are comments/empty)
    data_lines = []
    for line in lines[5:]:
        line = line.strip()
        if line and ',' in line:
            data_lines.append(line)
    
    print(f"Found {len(data_lines)} draws in backup file")
    
    # Data is newest first, ending date is Dec 6, 2025
    # Start date is Feb 27, 2023
    end_date = datetime(2025, 12, 6)
    start_date = datetime(2023, 2, 27)
    
    # Calculate expected days
    total_days = (end_date - start_date).days + 1
    print(f"Expected {total_days} days from {start_date.date()} to {end_date.date()}")
    
    draws = []
    current_date = end_date
    
    for line in data_lines:
        parts = line.split(',')
        if len(parts) == 6:
            main = sorted([int(x) for x in parts[:5]])
            bonus = int(parts[5])
            
            draws.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'main': main,
                'bonus': bonus
            })
            
            current_date -= timedelta(days=1)
    
    print(f"Generated {len(draws)} draws")
    print(f"Date range: {draws[-1]['date']} to {draws[0]['date']}")
    
    return draws

def main():
    draws = parse_backup()
    
    # Load existing data to get any newer draws
    try:
        with open(OUTPUT_FILE, 'r') as f:
            existing = json.load(f)
        existing_draws = existing.get('draws', [])
        
        # Find draws newer than Dec 6, 2025
        newer_draws = [d for d in existing_draws if d['date'] > '2025-12-06']
        print(f"Found {len(newer_draws)} newer draws to preserve")
        
        # Combine: newer draws first, then backfilled
        all_draws = newer_draws + draws
    except:
        all_draws = draws
    
    # Save
    output = {
        'name': 'Lucky for Life',
        'draws': all_draws,
        'lastUpdated': datetime.now().isoformat()
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ L4L data updated: {len(all_draws)} total draws")
    print(f"   Range: {all_draws[-1]['date']} to {all_draws[0]['date']}")

if __name__ == '__main__':
    main()
