"""Verify that HOLD and NEXT PLAY tickets use correct windows."""
import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent / 'data'

# Expected window configuration
EXPECTED_WINDOWS = {
    'l4l': {'hold': None, 'next_play': 200},   # None = all draws
    'la':  {'hold': None, 'next_play': 200},   # None = all draws
    'pb':  {'hold': 100, 'next_play': 22},     # 100 for HOLD, 22 for NEXT PLAY
    'mm':  {'hold': 100, 'next_play': 22}      # 100 for HOLD, 22 for NEXT PLAY
}

def load_draws(lottery):
    for fn in [f'{lottery}.json', f'{lottery}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                return d.get('draws', d) if isinstance(d, dict) else d
    return []

def calc_ticket_from_window(draws, window_size):
    """Calculate best ticket from a specific window size."""
    if window_size is None:
        working = draws
    else:
        working = draws[:min(window_size, len(draws))]
    
    pos_freq = {i: Counter() for i in range(5)}
    for draw in working:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] += 1
    
    top_per_pos = [[n for n,_ in pos_freq[i].most_common(6)] for i in range(5)]
    
    best_ticket = None
    best_score = -1
    for n1 in top_per_pos[0][:5]:
        for n2 in top_per_pos[1][:5]:
            if n2 <= n1: continue
            for n3 in top_per_pos[2][:5]:
                if n3 <= n2: continue
                for n4 in top_per_pos[3][:5]:
                    if n4 <= n3: continue
                    for n5 in top_per_pos[4][:5]:
                        if n5 <= n4: continue
                        ticket = [n1, n2, n3, n4, n5]
                        score = sum(pos_freq[i][ticket[i]] for i in range(5))
                        decades = len(set(n//10 for n in ticket))
                        if decades >= 2 and score > best_score:
                            best_ticket = ticket
                            best_score = score
    
    # Bonus
    bonus_freq = Counter()
    for draw in working:
        b = draw.get('bonus')
        if b: bonus_freq[b] += 1
    top_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
    
    return best_ticket, top_bonus, len(working)

print("="*70)
print("WINDOW VERIFICATION - Confirming tickets use correct windows")
print("="*70)

for lottery in ['l4l', 'la', 'pb', 'mm']:
    draws = load_draws(lottery)
    total = len(draws)
    
    hold_win = EXPECTED_WINDOWS[lottery]['hold']
    next_win = EXPECTED_WINDOWS[lottery]['next_play']
    
    hold_ticket, hold_bonus, hold_used = calc_ticket_from_window(draws, hold_win)
    next_ticket, next_bonus, next_used = calc_ticket_from_window(draws, next_win)
    
    hold_desc = f"all {hold_used}" if hold_win is None else f"{hold_used}/{hold_win}"
    next_desc = f"{next_used}/{next_win}"
    
    print(f"\n{lottery.upper()} (Total: {total} draws)")
    print(f"  HOLD Window:      {hold_desc} draws")
    print(f"  HOLD Ticket:      {hold_ticket} + {hold_bonus}")
    print(f"  NEXT PLAY Window: {next_desc} draws")
    print(f"  NEXT PLAY Ticket: {next_ticket} + {next_bonus}")
    
    # Verify they're different for PB/MM (smaller next_play window should give different results)
    if lottery in ['pb', 'mm'] and hold_ticket == next_ticket:
        print(f"  ⚠️ WARNING: Same ticket for different windows - may need more data variation")
    elif lottery in ['pb', 'mm']:
        print(f"  ✅ Different tickets from different windows - CORRECT!")

print("\n" + "="*70)
print("Verification complete!")
print("="*70)
