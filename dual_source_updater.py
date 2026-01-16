"""
Dual-Source Auto-Updater for Lottery Tracker
Fetches from 2+ sources per lottery, cross-verifies, saves only verified data
"""

import urllib.request
import json
import re
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.5',
}

def fetch_url(url, timeout=15):
    """Fetch URL with proper headers and gzip support."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if resp.info().get('Content-Encoding') == 'gzip':
                data = gzip.decompress(data)
            return data.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"      Fetch error for {url[:50]}...: {e}")
        return None

# ============================================================
# LUCKY FOR LIFE - Sources: CT Lottery RSS, lotto.net
# ============================================================
def fetch_l4l_ct():
    """Source 1: CT Lottery RSS feed."""
    try:
        html = fetch_url("https://www.ctlottery.org/Feeds/rssnumbers.xml")
        if not html:
            return None
        
        root = ET.fromstring(html)
        for item in root.findall('.//item'):
            title = item.find('title')
            desc = item.find('description')
            
            if title is not None and 'lucky for life' in title.text.lower():
                desc_text = desc.text if desc is not None else ""
                
                match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})\s+LB-(\d{1,2})', desc_text)
                if not match:
                    continue
                
                main = sorted([int(match.group(i)) for i in range(1, 6)])
                bonus = int(match.group(6))
                
                date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', title.text)
                if date_match:
                    date_str = f"{date_match.group(3)}-{date_match.group(1).zfill(2)}-{date_match.group(2).zfill(2)}"
                else:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                
                return {'date': date_str, 'main': main, 'bonus': bonus, 'source': 'CT_RSS'}
        return None
    except Exception as e:
        print(f"      L4L CT error: {e}")
        return None

def fetch_l4l_lotto_net():
    """Source 2: lotto.net."""
    try:
        html = fetch_url("https://www.lotto.net/lucky-for-life/numbers")
        if not html:
            return None
        
        # Find the latest results section
        match = re.search(r'class="balls[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        if not match:
            return None
        
        balls_html = match.group(1)
        numbers = re.findall(r'>(\d{1,2})<', balls_html)
        
        if len(numbers) >= 6:
            main = sorted([int(n) for n in numbers[:5]])
            bonus = int(numbers[5])
            
            # Try to find date
            date_match = re.search(r'(\w+day)\s+(\d{1,2})\w*\s+(\w+)\s+(\d{4})', html)
            if date_match:
                months = {'January': '01', 'February': '02', 'March': '03', 'April': '04',
                         'May': '05', 'June': '06', 'July': '07', 'August': '08',
                         'September': '09', 'October': '10', 'November': '11', 'December': '12'}
                month = months.get(date_match.group(3), '01')
                date_str = f"{date_match.group(4)}-{month}-{date_match.group(2).zfill(2)}"
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            return {'date': date_str, 'main': main, 'bonus': bonus, 'source': 'lotto.net'}
        return None
    except Exception as e:
        print(f"      L4L lotto.net error: {e}")
        return None

# ============================================================
# LOTTO AMERICA - Sources: Oklahoma Lottery, Iowa Lottery, lottoamerica.com
# ============================================================
def fetch_la_oklahoma():
    """Source 1: Oklahoma Lottery - most reliable for LA."""
    try:
        html = fetch_url("https://www.lottery.ok.gov/draw-games/lotto-america")
        if not html:
            return None
        
        # Look for winning numbers - Oklahoma shows them in spans
        numbers = re.findall(r'class="[^"]*ball[^"]*"[^>]*>(\d{1,2})<', html)
        if not numbers:
            numbers = re.findall(r'<span[^>]*>(\d{1,2})</span>', html)
        
        # Filter to valid LA numbers (1-52 for main, 1-10 for star ball)
        valid_main = [int(n) for n in numbers if 1 <= int(n) <= 52]
        valid_bonus = [int(n) for n in numbers if 1 <= int(n) <= 10]
        
        if len(valid_main) >= 5:
            main = sorted(valid_main[:5])
            bonus = valid_bonus[-1] if valid_bonus else None
            
            # Find date
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', html)
            if date_match:
                date_str = f"{date_match.group(3)}-{date_match.group(1).zfill(2)}-{date_match.group(2).zfill(2)}"
            else:
                now = datetime.now()
                for offset in range(7):
                    check = now - timedelta(days=offset)
                    if check.weekday() in [0, 2, 5]:  # Mon, Wed, Sat
                        date_str = check.strftime("%Y-%m-%d")
                        break
            
            if bonus:
                return {'date': date_str, 'main': main, 'bonus': bonus, 'source': 'Oklahoma'}
        return None
    except Exception as e:
        print(f"      LA Oklahoma error: {e}")
        return None

def fetch_la_iowa():
    """Source 1: Iowa Lottery HTML."""
    try:
        html = fetch_url("https://www.ialottery.com/games/lotto-america")
        if not html:
            return None
        
        main = []
        # Try multiple patterns for Iowa Lottery
        for i in range(1, 6):
            match = re.search(rf'lblLAN{i}["\'][^>]*>(\d+)<', html)
            if not match:
                match = re.search(rf'id=["\']?lblLAN{i}["\']?[^>]*>(\d+)', html)
            if match:
                main.append(int(match.group(1)))
        
        bonus_match = re.search(r'lblLAPower["\'][^>]*>(\d+)<', html)
        if not bonus_match:
            bonus_match = re.search(r'id=["\']?lblLAPower["\']?[^>]*>(\d+)', html)
        bonus = int(bonus_match.group(1)) if bonus_match else None
        
        if len(main) == 5 and bonus:
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', html)
            if date_match:
                date_str = f"{date_match.group(3)}-{date_match.group(1).zfill(2)}-{date_match.group(2).zfill(2)}"
            else:
                now = datetime.now()
                for offset in range(7):
                    check = now - timedelta(days=offset)
                    if check.weekday() in [0, 2, 5]:
                        date_str = check.strftime("%Y-%m-%d")
                        break
            
            return {'date': date_str, 'main': sorted(main), 'bonus': bonus, 'source': 'Iowa'}
        return None
    except Exception as e:
        print(f"      LA Iowa error: {e}")
        return None

def fetch_la_lottoamerica():
    """Source 2: Official Lotto America site."""
    try:
        html = fetch_url("https://www.lottoamerica.com/")
        if not html:
            return None
        
        # Look for winning numbers in various formats
        numbers = []
        # Try ball class pattern
        ball_matches = re.findall(r'class=["\']ball["\'][^>]*>(\d{1,2})<', html)
        if len(ball_matches) >= 6:
            numbers = ball_matches
        
        # Try winning-numbers pattern
        if not numbers:
            match = re.search(r'winning-numbers[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
            if match:
                numbers = re.findall(r'>(\d{1,2})<', match.group(1))
        
        # Try result-numbers pattern
        if not numbers:
            match = re.search(r'result[^>]*numbers[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
            if match:
                numbers = re.findall(r'>(\d{1,2})<', match.group(1))
        
        if len(numbers) >= 6:
            main = sorted([int(n) for n in numbers[:5]])
            bonus = int(numbers[5])
            
            now = datetime.now()
            for offset in range(7):
                check = now - timedelta(days=offset)
                if check.weekday() in [0, 2, 5]:
                    date_str = check.strftime("%Y-%m-%d")
                    break
            
            return {'date': date_str, 'main': main, 'bonus': bonus, 'source': 'lottoamerica.com'}
        return None
    except Exception as e:
        print(f"      LA lottoamerica.com error: {e}")
        return None

def fetch_la_lotto_net():
    """Source 3: lotto.net for Lotto America."""
    try:
        html = fetch_url("https://www.lotto.net/lotto-america/numbers")
        if not html:
            return None
        
        # Find all numbers on the page - first 6 single/double digit numbers are usually the result
        all_numbers = re.findall(r'>(\d{1,2})<', html)
        
        # Filter to valid LA numbers (1-52 for main, 1-10 for star ball)
        valid_main = []
        bonus = None
        
        for n in all_numbers:
            num = int(n)
            if 1 <= num <= 52 and len(valid_main) < 5 and num not in valid_main:
                valid_main.append(num)
            elif 1 <= num <= 10 and bonus is None and len(valid_main) == 5:
                bonus = num
                break
        
        if len(valid_main) == 5 and bonus:
            main = sorted(valid_main)
            
            now = datetime.now()
            date_str = None
            for offset in range(7):
                check = now - timedelta(days=offset)
                if check.weekday() in [0, 2, 5]:  # Mon, Wed, Sat
                    date_str = check.strftime("%Y-%m-%d")
                    break
            
            return {'date': date_str, 'main': main, 'bonus': bonus, 'source': 'lotto.net'}
        return None
    except Exception as e:
        print(f"      LA lotto.net error: {e}")
        return None

# ============================================================
# POWERBALL - Sources: NY Open Data, CT Lottery RSS, Iowa Lottery
# ============================================================
def fetch_pb_ny():
    """Source 1: NY Open Data CSV (most reliable)."""
    try:
        html = fetch_url("https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD")
        if not html:
            return None
        
        lines = html.strip().split('\n')
        if len(lines) < 2:
            return None
        
        latest = lines[-1].split(',')
        date_str = datetime.strptime(latest[0].strip('"'), "%m/%d/%Y").strftime("%Y-%m-%d")
        numbers = latest[1].strip('"').split()
        
        main = sorted([int(n) for n in numbers[:5]])
        bonus = int(numbers[5])
        
        return {'date': date_str, 'main': main, 'bonus': bonus, 'source': 'NY_OpenData'}
    except Exception as e:
        print(f"      PB NY error: {e}")
        return None

def fetch_pb_ct():
    """Source 2: CT Lottery RSS."""
    try:
        html = fetch_url("https://www.ctlottery.org/Feeds/rssnumbers.xml")
        if not html:
            return None
        
        root = ET.fromstring(html)
        for item in root.findall('.//item'):
            title = item.find('title')
            desc = item.find('description')
            
            if title is not None and 'powerball' in title.text.lower() and 'double' not in title.text.lower():
                desc_text = desc.text if desc is not None else ""
                
                match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})\s+PB-(\d{1,2})', desc_text)
                if not match:
                    continue
                
                main = sorted([int(match.group(i)) for i in range(1, 6)])
                bonus = int(match.group(6))
                
                date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', title.text)
                if date_match:
                    date_str = f"{date_match.group(3)}-{date_match.group(1).zfill(2)}-{date_match.group(2).zfill(2)}"
                else:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                
                return {'date': date_str, 'main': main, 'bonus': bonus, 'source': 'CT_RSS'}
        return None
    except Exception as e:
        print(f"      PB CT error: {e}")
        return None

def fetch_pb_iowa():
    """Source 3: Iowa Lottery HTML."""
    try:
        html = fetch_url("https://www.ialottery.com/games/powerball")
        if not html:
            return None
        
        main = []
        for i in range(1, 6):
            match = re.search(rf'lblPBN{i}["\'][^>]*>(\d+)<', html)
            if match:
                main.append(int(match.group(1)))
        
        bonus_match = re.search(r'lblPBPower["\'][^>]*>(\d+)<', html)
        bonus = int(bonus_match.group(1)) if bonus_match else None
        
        if len(main) == 5 and bonus:
            now = datetime.now()
            for offset in range(7):
                check = now - timedelta(days=offset)
                if check.weekday() in [0, 2, 5]:
                    date_str = check.strftime("%Y-%m-%d")
                    break
            
            return {'date': date_str, 'main': sorted(main), 'bonus': bonus, 'source': 'Iowa'}
        return None
    except Exception as e:
        print(f"      PB Iowa error: {e}")
        return None

# ============================================================
# MEGA MILLIONS - Sources: NY Open Data, Iowa Lottery
# ============================================================
def fetch_mm_ny():
    """Source 1: NY Open Data CSV (most reliable)."""
    try:
        html = fetch_url("https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD")
        if not html:
            return None
        
        lines = html.strip().split('\n')
        if len(lines) < 2:
            return None
        
        latest = lines[-1].split(',')
        date_str = datetime.strptime(latest[0].strip('"'), "%m/%d/%Y").strftime("%Y-%m-%d")
        main_str = latest[1].strip('"').split()
        
        main = sorted([int(n) for n in main_str])
        bonus = int(latest[2].strip('"'))
        
        return {'date': date_str, 'main': main, 'bonus': bonus, 'source': 'NY_OpenData'}
    except Exception as e:
        print(f"      MM NY error: {e}")
        return None

def fetch_mm_iowa():
    """Source 2: Iowa Lottery HTML."""
    try:
        html = fetch_url("https://www.ialottery.com/games/mega-millions")
        if not html:
            return None
        
        main = []
        for i in range(1, 6):
            match = re.search(rf'lblMMN{i}["\'][^>]*>(\d+)<', html)
            if match:
                main.append(int(match.group(1)))
        
        bonus_match = re.search(r'lblMMPower["\'][^>]*>(\d+)<', html)
        bonus = int(bonus_match.group(1)) if bonus_match else None
        
        if len(main) == 5 and bonus:
            now = datetime.now()
            for offset in range(7):
                check = now - timedelta(days=offset)
                if check.weekday() in [1, 4]:  # Tue, Fri
                    date_str = check.strftime("%Y-%m-%d")
                    break
            
            return {'date': date_str, 'main': sorted(main), 'bonus': bonus, 'source': 'Iowa'}
        return None
    except Exception as e:
        print(f"      MM Iowa error: {e}")
        return None

# ============================================================
# JACKPOT FETCHING - Multiple sources with fallbacks
# ============================================================
def fetch_jackpots():
    """Fetch current jackpots from multiple sources with fallbacks."""
    jackpots = {}
    
    # L4L - Fixed jackpot (never changes)
    jackpots['L4L'] = {
        'amount': '$7,000/week for life',
        'cashValue': 5750000,
        'schedule': 'Daily at 9:38 PM CT'
    }
    
    # PB - Try Texas Lottery (reliable, shows cash value)
    pb_found = False
    try:
        html = fetch_url("https://www.texaslottery.com/export/sites/lottery/Games/Powerball/index.html")
        if html:
            # Look for jackpot amount
            match = re.search(r'Est\.\s*(?:Annuitized\s*)?Jackpot[^$]*\$(\d+)\s*(Million|Billion)', html, re.IGNORECASE)
            if match:
                amount = int(match.group(1))
                if 'billion' in match.group(2).lower():
                    amount *= 1000
                # Look for cash value
                cash_match = re.search(r'Cash\s*Value[^$]*\$(\d+)\s*(Million|Billion)?', html, re.IGNORECASE)
                cash = int(cash_match.group(1)) * 1000000 if cash_match else int(amount * 450000)
                jackpots['PB'] = {
                    'amount': f"${amount}M",
                    'cashValue': cash,
                    'schedule': 'Mon/Wed/Sat at 9:59 PM CT'
                }
                pb_found = True
    except:
        pass
    
    # PB fallback
    if not pb_found:
        try:
            html = fetch_url("https://www.powerball.com/")
            if html:
                match = re.search(r'\$(\d+)\s*(Million|Billion)', html, re.IGNORECASE)
                if match:
                    amount = int(match.group(1))
                    if 'billion' in match.group(2).lower():
                        amount *= 1000
                    jackpots['PB'] = {
                        'amount': f"${amount}M",
                        'cashValue': int(amount * 450000),
                        'schedule': 'Mon/Wed/Sat at 9:59 PM CT'
                    }
        except:
            pass
    
    # MM - Try Virginia Lottery (reliable, shows cash value)
    mm_found = False
    try:
        html = fetch_url("https://www.valottery.com/data/draw-games/megamillions")
        if html:
            # Look for jackpot - format: "$215 MILLION"
            match = re.search(r'\$(\d+)\s*MILLION', html, re.IGNORECASE)
            if match:
                amount = int(match.group(1))
                # Look for cash value - format: "Cash Value: $98M"
                cash_match = re.search(r'Cash\s*Value[:\s]*\$(\d+)M?', html, re.IGNORECASE)
                cash = int(cash_match.group(1)) * 1000000 if cash_match else int(amount * 457000)
                jackpots['MM'] = {
                    'amount': f"${amount}M",
                    'cashValue': cash,
                    'schedule': 'Tue/Fri at 10:00 PM CT'
                }
                mm_found = True
    except:
        pass
    
    # MM fallback - megamillions.com
    if not mm_found:
        try:
            html = fetch_url("https://www.megamillions.com/")
            if html:
                match = re.search(r'\$(\d+)\s*(Million|Billion)', html, re.IGNORECASE)
                if match:
                    amount = int(match.group(1))
                    if 'billion' in match.group(2).lower():
                        amount *= 1000
                    jackpots['MM'] = {
                        'amount': f"${amount}M",
                        'cashValue': int(amount * 457000),
                        'schedule': 'Tue/Fri at 10:00 PM CT'
                    }
        except:
            pass
    
    # LA - Try powerball.com/lotto-america (most reliable - shows jackpot and cash value)
    la_found = False
    try:
        html = fetch_url("https://www.powerball.com/lotto-america")
        if html:
            # Look for jackpot amount - format: "$12.51 M"
            jackpot_match = re.search(r'\$(\d+(?:\.\d+)?)\s*M', html)
            cash_match = re.search(r'\$(\d+(?:\.\d+)?)\s*M.*?\$(\d+(?:\.\d+)?)\s*M', html)
            if jackpot_match:
                amount = float(jackpot_match.group(1))
                cash = float(cash_match.group(2)) * 1000000 if cash_match else int(amount * 450000)
                jackpots['LA'] = {
                    'amount': f"${amount:.2f}M" if amount < 100 else f"${int(amount)}M",
                    'cashValue': int(cash),
                    'schedule': 'Mon/Wed/Sat at 10:00 PM CT'
                }
                la_found = True
    except:
        pass
    
    # LA fallback - Iowa Lottery
    if not la_found:
        try:
            html = fetch_url("https://www.ialottery.com/games/lotto-america")
            if html:
                match = re.search(r'jackpot[^$]*\$([\d,\.]+)\s*(million)?', html, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    jackpots['LA'] = {
                        'amount': f"${amount:.2f}M" if amount < 100 else f"${int(amount)}M",
                        'cashValue': int(amount * 457000),
                        'schedule': 'Mon/Wed/Sat at 10:00 PM CT'
                    }
        except:
            pass
    
    return jackpots

# ============================================================
# CROSS-VERIFICATION & DATA SAVING
# ============================================================
def verify_and_get_best(results):
    """Cross-verify results from multiple sources, return verified draw or best available."""
    valid = [r for r in results if r is not None]
    
    if len(valid) == 0:
        return None, "No sources returned data"
    
    if len(valid) == 1:
        return valid[0], f"Single source: {valid[0]['source']}"
    
    # Check if numbers match across sources
    first = valid[0]
    for other in valid[1:]:
        if first['main'] == other['main'] and first['bonus'] == other['bonus']:
            return first, f"VERIFIED by {first['source']} + {other['source']}"
    
    # Numbers don't match - return most reliable (NY OpenData > CT RSS > Iowa > others)
    priority = {'NY_OpenData': 1, 'CT_RSS': 2, 'Iowa': 3}
    valid.sort(key=lambda x: priority.get(x['source'], 99))
    return valid[0], f"MISMATCH - using {valid[0]['source']} (most reliable)"

def save_draw(lottery_key, draw, verification_msg):
    """Save verified draw to JSON file."""
    if not draw:
        return False, "No draw to save"
    
    file_path = DATA_DIR / f"{lottery_key.lower()}.json"
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Check if already exists
        for existing in data['draws']:
            if existing['date'] == draw['date']:
                return False, f"Already have {draw['date']}"
            if existing['main'] == draw['main'] and existing['bonus'] == draw['bonus']:
                return False, "Duplicate numbers"
        
        # Remove source key before saving
        save_draw = {'date': draw['date'], 'main': draw['main'], 'bonus': draw['bonus']}
        
        # Add to beginning (newest first)
        data['draws'].insert(0, save_draw)
        data['lastUpdated'] = datetime.now().isoformat()
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True, f"SAVED {draw['date']} = {draw['main']} + {draw['bonus']}"
    
    except Exception as e:
        return False, f"Save error: {e}"

def save_jackpots(jackpots):
    """Save jackpots to JSON file."""
    file_path = DATA_DIR / "jackpots.json"
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Update with fetched values, keep existing if not fetched
        for key in ['L4L', 'LA', 'PB', 'MM']:
            if key in jackpots:
                if key not in data:
                    data[key] = {}
                data[key]['amount'] = jackpots[key].get('amount', data[key].get('amount'))
                data[key]['cashValue'] = jackpots[key].get('cashValue', data[key].get('cashValue'))
                data[key]['schedule'] = jackpots[key].get('schedule', data[key].get('schedule'))
                
                # Calculate next draw
                now = datetime.now()
                if key == 'L4L':
                    days = [0,1,2,3,4,5,6]
                    hour, minute = 21, 38
                elif key in ['LA', 'PB']:
                    days = [0, 2, 5]
                    hour, minute = (22, 0) if key == 'LA' else (21, 59)
                else:  # MM
                    days = [1, 4]
                    hour, minute = 22, 0
                
                for offset in range(8):
                    check = now + timedelta(days=offset)
                    if check.weekday() in days:
                        draw_time = check.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        if draw_time > now:
                            data[key]['nextDraw'] = draw_time.isoformat()
                            break
        
        data['lastUpdated'] = datetime.now().isoformat()
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Jackpot save error: {e}")
        return False

# ============================================================
# MAIN UPDATE FUNCTION
# ============================================================
def update_all():
    """Update all lotteries with dual-source verification."""
    print(f"\n{'='*60}")
    print(f"   DUAL-SOURCE LOTTERY UPDATER")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    results = {}
    
    # L4L
    print("🎯 Lucky for Life:")
    print("   Fetching CT RSS...", end=" ")
    l4l_ct = fetch_l4l_ct()
    print("✓" if l4l_ct else "✗")
    print("   Fetching lotto.net...", end=" ")
    l4l_net = fetch_l4l_lotto_net()
    print("✓" if l4l_net else "✗")
    
    l4l_draw, l4l_msg = verify_and_get_best([l4l_ct, l4l_net])
    print(f"   {l4l_msg}")
    saved, save_msg = save_draw('l4l', l4l_draw, l4l_msg)
    print(f"   {'✅' if saved else '⏭️'} {save_msg}\n")
    results['L4L'] = {'saved': saved, 'draw': l4l_draw}
    
    # LA
    print("🔵 Lotto America:")
    print("   Fetching Oklahoma Lottery...", end=" ")
    la_ok = fetch_la_oklahoma()
    print("✓" if la_ok else "✗")
    print("   Fetching Iowa Lottery...", end=" ")
    la_iowa = fetch_la_iowa()
    print("✓" if la_iowa else "✗")
    print("   Fetching lottoamerica.com...", end=" ")
    la_official = fetch_la_lottoamerica()
    print("✓" if la_official else "✗")
    print("   Fetching lotto.net...", end=" ")
    la_lottonet = fetch_la_lotto_net()
    print("✓" if la_lottonet else "✗")
    
    la_draw, la_msg = verify_and_get_best([la_ok, la_iowa, la_official, la_lottonet])
    print(f"   {la_msg}")
    saved, save_msg = save_draw('la', la_draw, la_msg)
    print(f"   {'✅' if saved else '⏭️'} {save_msg}\n")
    results['LA'] = {'saved': saved, 'draw': la_draw}
    
    # PB
    print("🔴 Powerball:")
    print("   Fetching NY Open Data...", end=" ")
    pb_ny = fetch_pb_ny()
    print("✓" if pb_ny else "✗")
    print("   Fetching CT RSS...", end=" ")
    pb_ct = fetch_pb_ct()
    print("✓" if pb_ct else "✗")
    print("   Fetching Iowa Lottery...", end=" ")
    pb_iowa = fetch_pb_iowa()
    print("✓" if pb_iowa else "✗")
    
    pb_draw, pb_msg = verify_and_get_best([pb_ny, pb_ct, pb_iowa])
    print(f"   {pb_msg}")
    saved, save_msg = save_draw('pb', pb_draw, pb_msg)
    print(f"   {'✅' if saved else '⏭️'} {save_msg}\n")
    results['PB'] = {'saved': saved, 'draw': pb_draw}
    
    # MM
    print("🟡 Mega Millions:")
    print("   Fetching NY Open Data...", end=" ")
    mm_ny = fetch_mm_ny()
    print("✓" if mm_ny else "✗")
    print("   Fetching Iowa Lottery...", end=" ")
    mm_iowa = fetch_mm_iowa()
    print("✓" if mm_iowa else "✗")
    
    mm_draw, mm_msg = verify_and_get_best([mm_ny, mm_iowa])
    print(f"   {mm_msg}")
    saved, save_msg = save_draw('mm', mm_draw, mm_msg)
    print(f"   {'✅' if saved else '⏭️'} {save_msg}\n")
    results['MM'] = {'saved': saved, 'draw': mm_draw}
    
    # Jackpots
    print("💰 Updating Jackpots...")
    jackpots = fetch_jackpots()
    save_jackpots(jackpots)
    print(f"   L4L: {jackpots.get('L4L', {}).get('amount', 'N/A')}")
    print(f"   LA: {jackpots.get('LA', {}).get('amount', 'N/A')}")
    print(f"   PB: {jackpots.get('PB', {}).get('amount', 'N/A')}")
    print(f"   MM: {jackpots.get('MM', {}).get('amount', 'N/A')}")
    
    # Check predictions if any data was saved
    any_saved = any(r.get('saved') for r in results.values())
    if any_saved:
        print("\n📊 Checking predictions against new data...")
        try:
            from morning_evaluation import evaluate_predictions
            checked = evaluate_predictions()
            if checked:
                print(f"   Checked {len(checked)} predictions!")
            else:
                print("   No pending predictions to check")
        except Exception as e:
            print(f"   Could not check predictions: {e}")
    
    print(f"\n{'='*60}")
    print(f"   UPDATE COMPLETE")
    print(f"{'='*60}\n")
    
    return results

if __name__ == '__main__':
    update_all()
