"""Check if tied tickets have ever hit 5/5 and calculate combined odds."""
import json
from pathlib import Path

DATA_DIR = Path('data')

def load_draws(lottery):
    for fn in [f'{lottery}_historical_data.json', f'{lottery}.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                return json.load(f).get('draws', [])
    return []

# All tied tickets
tied_tickets = {
    'l4l': [[1, 12, 30, 39, 47]],
    'la': [[1, 15, 23, 42, 51], [1, 15, 27, 42, 51]],
    'pb': [[1, 11, 33, 52, 69]],
    'mm': [[6, 10, 27, 42, 68], [6, 21, 27, 42, 68], [6, 18, 27, 42, 68]]
}

print("=" * 70)
print("CHECKING IF TIED TICKETS EVER HIT 5/5 (JACKPOT)")
print("=" * 70)

for lottery, tickets in tied_tickets.items():
    draws = load_draws(lottery)
    print(f"\n{lottery.upper()} ({len(draws)} draws):")
    
    for ticket in tickets:
        best_match = 0
        hit_5 = False
        
        for draw in draws:
            main = sorted(draw.get('main', []))
            match_count = len(set(ticket) & set(main))
            if match_count > best_match:
                best_match = match_count
            if match_count == 5:
                hit_5 = True
                print(f"  {ticket} - HIT 5/5 on {draw.get('date', 'unknown')}!")
        
        if not hit_5:
            print(f"  {ticket} - NEVER hit 5/5. Best: {best_match}/5")

print("\n" + "=" * 70)
print("COMBINED ODDS WHEN PLAYING MULTIPLE TIED TICKETS")
print("=" * 70)

# Base odds and improvements
LA_BASE = 29144841
MM_BASE = 302575350
LA_IMP = 2.62
MM_IMP = 2.5

la_single = LA_BASE / LA_IMP
mm_single = MM_BASE / MM_IMP

print(f"\nLOTTO AMERICA (2 tied tickets at $1 each):")
print(f"  Single ticket: 1 in {int(la_single):,}")
print(f"  Playing BOTH:  1 in {int(la_single/2):,} (2x better)")
print(f"  Cost per draw: $2")

print(f"\nMEGA MILLIONS (3 tied tickets at $5 each):")
print(f"  Single ticket: 1 in {int(mm_single):,}")
print(f"  Playing ALL 3: 1 in {int(mm_single/3):,} (3x better)")
print(f"  Cost per draw: $15")

print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)
print("\nLA: Play BOTH tied tickets - doubles your odds for only $2/draw")
print("MM: Consider playing 1-2 of the 3 tied tickets ($5-10 vs $15)")
