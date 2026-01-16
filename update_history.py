"""
Backfill and update Powerball and Mega Millions historical draws
Source: NY Open Data CSV feeds
"""

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request

DATA_DIR = Path(__file__).parent / 'data'

CONFIG = {
    'PB': {
        'filename': 'pb.json',
        'url': 'https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD',
        'start_date': datetime(2020, 1, 1),
        'type': 'powerball'
    },
    'MM': {
        'filename': 'mm.json',
        'url': 'https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD',
        'start_date': datetime(2020, 1, 1),
        'type': 'megamillions'
    }
}


def fetch_csv_text(url: str) -> str:
    """Download CSV text from NY Open Data with user-agent."""
    req = Request(url, headers={'User-Agent': 'LotteryTracker/1.0'})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')


def parse_draws(lottery_key: str, csv_text: str) -> list:
    """Parse CSV text into draw objects sorted newest-first."""
    cfg = CONFIG[lottery_key]
    reader = csv.DictReader(io.StringIO(csv_text))

    draws = []
    seen_dates = set()

    for row in reader:
        date_str = row['Draw Date'].strip()
        try:
            draw_date = datetime.strptime(date_str, '%m/%d/%Y')
        except ValueError:
            continue

        if draw_date < cfg['start_date']:
            continue

        iso_date = draw_date.strftime('%Y-%m-%d')
        if iso_date in seen_dates:
            continue

        if cfg['type'] == 'powerball':
            numbers = row['Winning Numbers'].strip().split()
            if len(numbers) < 6:
                continue
            main = list(map(int, numbers[:5]))
            bonus = int(numbers[5])
        else:  # Mega Millions
            numbers = row['Winning Numbers'].strip().split()
            if len(numbers) < 5 or not row.get('Mega Ball'):
                continue
            main = list(map(int, numbers[:5]))
            bonus = int(row['Mega Ball'])

        draws.append({
            'date': iso_date,
            'main': main,
            'bonus': bonus
        })
        seen_dates.add(iso_date)

    draws.sort(key=lambda d: d['date'], reverse=True)
    return draws


def update_lottery(lottery_key: str):
    cfg = CONFIG[lottery_key]
    print(f"\n{'='*70}")
    print(f"Updating {lottery_key} from {cfg['url']}")
    csv_text = fetch_csv_text(cfg['url'])
    draws = parse_draws(lottery_key, csv_text)
    print(f"Parsed {len(draws)} draws (since {cfg['start_date'].date()})")

    file_path = DATA_DIR / cfg['filename']
    with open(file_path, 'r') as f:
        existing = json.load(f)

    existing['draws'] = draws
    existing['lastUpdated'] = datetime.now().isoformat()

    with open(file_path, 'w') as f:
        json.dump(existing, f, indent=2)

    print(f"✅ {lottery_key} history updated. Latest: {draws[0]['date']}, Oldest: {draws[-1]['date']}")


def main():
    for key in CONFIG:
        update_lottery(key)
    print("\nAll histories updated!")


if __name__ == '__main__':
    main()
