"""
Auto-updater for Lottery Tracker
Fetches latest draws from official sources every 30 minutes
"""

import urllib.request
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

def fetch_l4l():
    """Fetch latest Lucky for Life draw from CT Lottery RSS."""
    try:
        url = "https://www.ctlottery.org/Feeds/rssnumbers.xml"
        with urllib.request.urlopen(url, timeout=10) as resp:
            xml_data = resp.read()
        
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item'):
            title = item.find('title')
            description = item.find('description')
            
            if title is not None and 'lucky for life' in title.text.lower():
                desc_text = description.text if description is not None else ""
                
                # Parse numbers
                match = re.search(r'(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})\s+LB-(\d{2})', desc_text)
                if not match:
                    continue
                
                main = sorted([int(match.group(i)) for i in range(1, 6)])
                bonus = int(match.group(6))
                
                # Parse date
                date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', title.text)
                if date_match:
                    date_str = f"{date_match.group(3)}-{date_match.group(1)}-{date_match.group(2)}"
                else:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                
                return {'date': date_str, 'main': main, 'bonus': bonus}
        
        return None
    except Exception as e:
        print(f"L4L fetch error: {e}")
        return None

def fetch_la():
    """Fetch latest Lotto America draw from Iowa Lottery."""
    try:
        url = "https://www.ialottery.com/games/lotto-america"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
        
        # Look for label pattern: lblLAN1 through lblLAN5, lblLAPower
        main = []
        for i in range(1, 6):
            match = re.search(f'lblLAN{i}["\']>(\d+)<', html)
            if match:
                main.append(int(match.group(1)))
        
        bonus_match = re.search(r'lblLAPower["\']>(\d+)<', html)
        bonus = int(bonus_match.group(1)) if bonus_match else None
        
        if len(main) == 5 and bonus:
            # Iowa doesn't always show date clearly, use current date
            date_str = datetime.now().strftime("%Y-%m-%d")
            return {'date': date_str, 'main': sorted(main), 'bonus': bonus}
        
        return None
    except Exception as e:
        print(f"LA fetch error: {e}")
        return None

def fetch_pb():
    """Fetch latest Powerball draw from NY Open Data."""
    try:
        url = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = resp.read().decode('utf-8')
        
        lines = data.strip().split('\n')
        if len(lines) < 2:
            return None
        
        # CSV is oldest first, so get LAST line (most recent)
        latest = lines[-1].split(',')
        
        # Format: "Draw Date","Winning Numbers","Multiplier"
        # Example: "01/06/2026","12 24 36 48 60 15","2"
        date_str = datetime.strptime(latest[0].strip('"'), "%m/%d/%Y").strftime("%Y-%m-%d")
        numbers = latest[1].strip('"').split()
        
        main = sorted([int(n) for n in numbers[:5]])
        bonus = int(numbers[5])
        
        return {'date': date_str, 'main': main, 'bonus': bonus}
    except Exception as e:
        print(f"PB fetch error: {e}")
        return None

def fetch_mm():
    """Fetch latest Mega Millions draw from NY Open Data."""
    try:
        url = "https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD"
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = resp.read().decode('utf-8')
        
        lines = data.strip().split('\n')
        if len(lines) < 2:
            return None
        
        # CSV is oldest first, so get LAST line (most recent)
        latest = lines[-1].split(',')
        
        # Format: "Draw Date","Winning Numbers","Mega Ball","Multiplier"
        date_str = datetime.strptime(latest[0].strip('"'), "%m/%d/%Y").strftime("%Y-%m-%d")
        main_str = latest[1].strip('"').split()
        
        main = sorted([int(n) for n in main_str])
        bonus = int(latest[2].strip('"'))
        
        return {'date': date_str, 'main': main, 'bonus': bonus}
    except Exception as e:
        print(f"MM fetch error: {e}")
        return None

def update_lottery_data(lottery_key, new_draw):
    """Update lottery JSON file if draw is new."""
    if not new_draw:
        return False, "No data fetched"
    
    file_path = DATA_DIR / f"{lottery_key.lower()}.json"
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Check if this draw already exists
        for draw in data['draws']:
            if draw['date'] == new_draw['date']:
                return False, f"Already have {new_draw['date']}"
            if draw['main'] == new_draw['main'] and draw['bonus'] == new_draw['bonus']:
                return False, "Duplicate numbers"
        
        # Add new draw at the beginning (newest first)
        data['draws'].insert(0, new_draw)
        data['lastUpdated'] = datetime.now().isoformat()
        
        # Keep ALL draws - historical data is important!
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True, f"Added {new_draw['date']}"
    
    except Exception as e:
        return False, f"Error: {e}"

def update_all():
    """Update all 4 lotteries."""
    print(f"\n{'='*60}")
    print(f"🔄 LOTTERY TRACKER AUTO-UPDATE")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    results = {}
    
    # L4L
    print("🎯 Lucky for Life...", end=" ")
    l4l_draw = fetch_l4l()
    success, msg = update_lottery_data('l4l', l4l_draw)
    results['L4L'] = {'success': success, 'message': msg, 'draw': l4l_draw}
    print(f"{'✅' if success else '⏭️'} {msg}")
    
    # LA
    print("🔵 Lotto America...", end=" ")
    la_draw = fetch_la()
    success, msg = update_lottery_data('la', la_draw)
    results['LA'] = {'success': success, 'message': msg, 'draw': la_draw}
    print(f"{'✅' if success else '⏭️'} {msg}")
    
    # PB
    print("🔴 Powerball...", end=" ")
    pb_draw = fetch_pb()
    success, msg = update_lottery_data('pb', pb_draw)
    results['PB'] = {'success': success, 'message': msg, 'draw': pb_draw}
    print(f"{'✅' if success else '⏭️'} {msg}")
    
    # MM
    print("🟡 Mega Millions...", end=" ")
    mm_draw = fetch_mm()
    success, msg = update_lottery_data('mm', mm_draw)
    results['MM'] = {'success': success, 'message': msg, 'draw': mm_draw}
    print(f"{'✅' if success else '⏭️'} {msg}")
    
    print(f"\n{'='*60}")
    print(f"✅ Update complete")
    print(f"{'='*60}\n")
    
    return results

if __name__ == '__main__':
    update_all()
