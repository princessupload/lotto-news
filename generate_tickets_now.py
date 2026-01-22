"""Generate current HOLD and NEXT PLAY tickets for all lotteries."""
import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent / 'data'

# Window configuration (updated Jan 21, 2026)
WINDOWS = {
    'l4l': {'hold': None, 'next_play': 200},   # All draws for HOLD
    'la':  {'hold': None, 'next_play': 200},   # All draws for HOLD
    'pb':  {'hold': 100, 'next_play': 35},     # 100 for HOLD, 35 for NEXT PLAY
    'mm':  {'hold': 100, 'next_play': 35}      # 100 for HOLD, 35 for NEXT PLAY
}

NAMES = {
    'l4l': 'Lucky for Life',
    'la': 'Lotto America', 
    'pb': 'Powerball',
    'mm': 'Mega Millions'
}

def load_draws(lottery):
    for fn in [f'{lottery}.json', f'{lottery}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                return d.get('draws', d) if isinstance(d, dict) else d
    return []

def generate_hold_ticket(draws, window):
    """Generate HOLD ticket from specified window."""
    if window is None:
        working = draws
    else:
        working = draws[:min(window, len(draws))]
    
    if len(working) < 50:
        return None, None, len(working)
    
    pos_freq = {i: Counter() for i in range(5)}
    for draw in working:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] += 1
    
    # Get top candidates per position
    top_per_pos = [[n for n, _ in pos_freq[i].most_common(8)] for i in range(5)]
    
    best_ticket = None
    best_score = -1
    
    for n1 in top_per_pos[0][:6]:
        for n2 in top_per_pos[1][:6]:
            if n2 <= n1: continue
            for n3 in top_per_pos[2][:6]:
                if n3 <= n2: continue
                for n4 in top_per_pos[3][:6]:
                    if n4 <= n3: continue
                    for n5 in top_per_pos[4][:6]:
                        if n5 <= n4: continue
                        ticket = [n1, n2, n3, n4, n5]
                        score = sum(pos_freq[i][ticket[i]] for i in range(5))
                        decades = len(set(n//10 for n in ticket))
                        consecutive = sum(1 for i in range(4) if ticket[i+1] - ticket[i] == 1)
                        if decades >= 2 and consecutive <= 1 and score > best_score:
                            best_ticket = ticket
                            best_score = score
    
    bonus_freq = Counter()
    for draw in working:
        b = draw.get('bonus')
        if b: bonus_freq[b] += 1
    top_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
    
    return best_ticket, top_bonus, len(working)

def generate_next_play_ticket(draws, window):
    """Generate NEXT PLAY ticket from specified window."""
    working = draws[:min(window, len(draws))]
    
    if len(working) < 10:
        return None, None, len(working)
    
    pos_freq = {i: Counter() for i in range(5)}
    for draw in working:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] += 1
    
    # Get top number per position (no duplicates)
    ticket = []
    used = set()
    for i in range(5):
        for num, _ in pos_freq[i].most_common(10):
            if num not in used:
                ticket.append(num)
                used.add(num)
                break
    
    if len(ticket) < 5:
        return None, None, len(working)
    
    bonus_freq = Counter()
    for draw in working:
        b = draw.get('bonus')
        if b: bonus_freq[b] += 1
    top_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
    
    return sorted(ticket), top_bonus, len(working)

print("=" * 70)
print("LOTTERY TICKETS - Generated Jan 21, 2026")
print("=" * 70)

print("\n" + "=" * 70)
print("HOLD TICKETS (Play these consistently)")
print("=" * 70)

for lottery in ['l4l', 'la', 'pb', 'mm']:
    draws = load_draws(lottery)
    window = WINDOWS[lottery]['hold']
    ticket, bonus, used = generate_hold_ticket(draws, window)
    window_desc = f"all {used}" if window is None else f"{used}/{window}"
    print(f"\n{NAMES[lottery].upper()}")
    print(f"  Ticket: {ticket} + Bonus: {bonus}")
    print(f"  Window: {window_desc} draws")

print("\n" + "=" * 70)
print("NEXT PLAY TICKETS (Play once, regenerated daily)")
print("=" * 70)

for lottery in ['l4l', 'la', 'pb', 'mm']:
    draws = load_draws(lottery)
    window = WINDOWS[lottery]['next_play']
    ticket, bonus, used = generate_next_play_ticket(draws, window)
    print(f"\n{NAMES[lottery].upper()}")
    print(f"  Ticket: {ticket} + Bonus: {bonus}")
    print(f"  Window: {used}/{window} draws")

print("\n" + "=" * 70)
print("Tonight's Results (Jan 21, 2026)")
print("=" * 70)
print("Powerball: [11, 26, 27, 53, 55] + PB: 12")
print("Lucky for Life: [3, 10, 22, 32, 38] + LB: 11")
print("\nNext draws: PB Sat Jan 25, MM Fri Jan 24, L4L daily, LA Wed Jan 22")
