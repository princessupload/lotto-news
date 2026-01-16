"""
Migrate historical data from lottery-guide to lottery-tracker
Keeps last 100 draws for each lottery
"""

import json
from pathlib import Path
from datetime import datetime

OLD_DIR = Path("../lottery-guide")
NEW_DIR = Path("data")

def migrate_lottery(old_file, new_file, lottery_name, abbr):
    """Migrate one lottery's data."""
    old_path = OLD_DIR / old_file
    new_path = NEW_DIR / new_file
    
    try:
        # Load old data
        with open(old_path, 'r') as f:
            old_data = json.load(f)
        
        # Get ALL draws (most recent first)
        draws = old_data.get('draws', [])
        draws.reverse()  # Most recent first (was oldest first)
        
        # Format for new structure
        new_data = {
            'lottery': lottery_name,
            'abbreviation': abbr,
            'draws': [
                {
                    'date': draw['date'],
                    'main': draw['main'],
                    'bonus': draw['bonus']
                }
                for draw in draws
            ],
            'lastUpdated': datetime.now().isoformat()
        }
        
        # Save new data
        with open(new_path, 'w') as f:
            json.dump(new_data, f, indent=2)
        
        print(f"✅ {abbr}: Migrated {len(new_data['draws'])} draws")
        return True
        
    except FileNotFoundError:
        print(f"⚠️  {abbr}: Old file not found: {old_path}")
        return False
    except Exception as e:
        print(f"❌ {abbr}: Error: {e}")
        return False

def main():
    print("=" * 60)
    print("MIGRATING HISTORICAL DATA")
    print("=" * 60)
    print()
    
    # Migrate all 4 lotteries
    migrate_lottery('l4l_historical_data.json', 'l4l.json', 'Lucky for Life', 'L4L')
    migrate_lottery('la_historical_data.json', 'la.json', 'Lotto America', 'LA')
    migrate_lottery('pb_historical_data.json', 'pb.json', 'Powerball', 'PB')
    migrate_lottery('mm_historical_data.json', 'mm.json', 'Mega Millions', 'MM')
    
    print()
    print("=" * 60)
    print("✅ Migration complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
