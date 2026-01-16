"""
DEEP PATTERN ANALYSIS
Critical examination of:
1. Do exact jackpots ever repeat?
2. Do 5/5, 4/5, 3/5, 2/5, 1/5 matches repeat between draws?
3. Column-level repeating patterns and cycles
4. Verify all our discoveries are accurate
"""
import json
from collections import Counter, defaultdict
from pathlib import Path
from itertools import combinations

DATA_DIR = Path(__file__).parent / 'data'

lotteries = {
    'l4l': 'Lucky for Life',
    'la': 'Lotto America', 
    'pb': 'Powerball',
    'mm': 'Mega Millions'
}

print("=" * 80)
print("DEEP PATTERN ANALYSIS - CRITICAL EXAMINATION")
print("=" * 80)

for lot, name in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        data = json.load(f)
    draws = data['draws']
    
    print(f"\n{'='*80}")
    print(f"{name.upper()} ({len(draws)} draws)")
    print(f"{'='*80}")
    
    # 1. EXACT JACKPOT REPEATS - Has the same exact ticket ever won twice?
    print(f"\n--- EXACT TICKET REPEATS ---")
    ticket_counts = Counter()
    for d in draws:
        ticket = tuple(sorted(d['main']))
        ticket_counts[ticket] += 1
    
    repeats = [(t, c) for t, c in ticket_counts.items() if c > 1]
    if repeats:
        print(f"  WARNING: FOUND {len(repeats)} EXACT TICKET REPEATS!")
        for ticket, count in repeats[:5]:
            print(f"     {list(ticket)} appeared {count} times")
    else:
        print(f"  OK: No exact ticket has ever repeated (all {len(draws)} unique)")
    
    # With bonus
    full_ticket_counts = Counter()
    for d in draws:
        ticket = (tuple(sorted(d['main'])), d.get('bonus'))
        full_ticket_counts[ticket] += 1
    
    full_repeats = [(t, c) for t, c in full_ticket_counts.items() if c > 1]
    if full_repeats:
        print(f"  WARNING: FOUND {len(full_repeats)} EXACT JACKPOT REPEATS (with bonus)!")
    else:
        print(f"  OK: No exact jackpot (5+bonus) has ever repeated")
    
    # 2. MATCH LEVEL ANALYSIS - How often do consecutive draws share X numbers?
    print(f"\n--- CONSECUTIVE DRAW MATCH ANALYSIS ---")
    match_counts = Counter()
    for i in range(len(draws) - 1):
        current = set(draws[i]['main'])
        prev = set(draws[i+1]['main'])
        matches = len(current & prev)
        match_counts[matches] += 1
    
    print(f"  Matches between consecutive draws:")
    for m in range(6):
        count = match_counts.get(m, 0)
        pct = count / (len(draws)-1) * 100
        bar = "#" * int(pct/2)
        print(f"    {m}/5: {count:4d} times ({pct:5.1f}%) {bar}")
    
    # 3. DO HIGH-MATCH PATTERNS REPEAT? (Same 3/5, 4/5, 5/5 appearing again)
    print(f"\n--- DO HIGH-MATCH COMBOS REPEAT? ---")
    
    # Track all 3-number, 4-number, 5-number combos
    combo_3 = Counter()
    combo_4 = Counter()
    combo_5 = Counter()
    
    for d in draws:
        main = tuple(sorted(d['main']))
        combo_5[main] += 1
        for c4 in combinations(main, 4):
            combo_4[c4] += 1
        for c3 in combinations(main, 3):
            combo_3[c3] += 1
    
    # How many 3-combos appear multiple times?
    repeat_3 = sum(1 for c, cnt in combo_3.items() if cnt > 1)
    repeat_4 = sum(1 for c, cnt in combo_4.items() if cnt > 1)
    repeat_5 = sum(1 for c, cnt in combo_5.items() if cnt > 1)
    
    max_repeat_3 = max(combo_3.values())
    max_repeat_4 = max(combo_4.values()) if combo_4 else 0
    max_repeat_5 = max(combo_5.values()) if combo_5 else 0
    
    top_3 = combo_3.most_common(3)
    top_4 = combo_4.most_common(3)
    
    print(f"  3-number combos that repeat: {repeat_3} (max {max_repeat_3} times)")
    print(f"    Top 3: {[list(c) for c, _ in top_3]} appeared {[cnt for _, cnt in top_3]} times")
    print(f"  4-number combos that repeat: {repeat_4} (max {max_repeat_4} times)")
    if top_4:
        print(f"    Top 4: {[list(c) for c, _ in top_4]} appeared {[cnt for _, cnt in top_4]} times")
    print(f"  5-number combos that repeat: {repeat_5} (max {max_repeat_5} times)")
    
    # 4. COLUMN/POSITION CYCLE ANALYSIS
    print(f"\n--- POSITION CYCLE ANALYSIS ---")
    
    for pos in range(5):
        pos_numbers = [sorted(d['main'])[pos] for d in draws]
        
        # Check for exact position repeats (same number in same position consecutively)
        pos_repeats = sum(1 for i in range(len(pos_numbers)-1) if pos_numbers[i] == pos_numbers[i+1])
        
        # Check for cycles (number returns to same position within N draws)
        cycle_counts = defaultdict(int)
        for i, num in enumerate(pos_numbers):
            # Find next occurrence of same number in same position
            for j in range(i+1, min(i+50, len(pos_numbers))):
                if pos_numbers[j] == num:
                    cycle_counts[j-i] += 1
                    break
        
        top_cycles = sorted(cycle_counts.items(), key=lambda x: -x[1])[:3]
        
        print(f"  Position {pos+1}:")
        print(f"    Consecutive repeats: {pos_repeats} ({pos_repeats/(len(draws)-1)*100:.1f}%)")
        if top_cycles:
            print(f"    Most common cycles: {top_cycles}")
    
    # 5. BONUS BALL REPEATS
    print(f"\n--- BONUS BALL CONSECUTIVE REPEATS ---")
    bonus_list = [d.get('bonus') for d in draws if d.get('bonus')]
    bonus_repeats = sum(1 for i in range(len(bonus_list)-1) if bonus_list[i] == bonus_list[i+1])
    print(f"  Consecutive bonus repeats: {bonus_repeats} ({bonus_repeats/(len(bonus_list)-1)*100:.1f}%)")
    
    # 6. GAP ANALYSIS - How long until a number returns?
    print(f"\n--- NUMBER RETURN GAP ANALYSIS ---")
    all_numbers = set(n for d in draws for n in d['main'])
    gap_stats = []
    
    for num in sorted(all_numbers)[:10]:  # Sample first 10 numbers
        appearances = [i for i, d in enumerate(draws) if num in d['main']]
        if len(appearances) > 1:
            gaps = [appearances[i+1] - appearances[i] for i in range(len(appearances)-1)]
            avg_gap = sum(gaps) / len(gaps)
            gap_stats.append((num, avg_gap, min(gaps), max(gaps)))
    
    print(f"  Sample number return gaps (draws between appearances):")
    for num, avg, mn, mx in gap_stats[:5]:
        print(f"    Number {num}: avg={avg:.1f}, min={mn}, max={mx}")

print("\n" + "=" * 80)
print("CRITICAL VERIFICATION OF OUR DISCOVERIES")
print("=" * 80)

# Verify decade spread claim
print("\n--- VERIFYING DECADE SPREAD CLAIM ---")
for lot, name in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        draws = json.load(f)['draws']
    
    decade_counts = Counter()
    for d in draws:
        decades = len(set(n // 10 for n in d['main']))
        decade_counts[decades] += 1
    
    total = len(draws)
    pct_3_plus = sum(decade_counts[d] for d in decade_counts if d >= 3) / total * 100
    
    print(f"  {name}: {pct_3_plus:.1f}% have 3+ decades")
    for dec in sorted(decade_counts.keys()):
        print(f"    {dec} decades: {decade_counts[dec]} ({decade_counts[dec]/total*100:.1f}%)")

# Verify consecutive claim
print("\n--- VERIFYING CONSECUTIVE NUMBERS CLAIM ---")
for lot, name in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        draws = json.load(f)['draws']
    
    consec_counts = Counter()
    for d in draws:
        main = sorted(d['main'])
        consecs = sum(1 for i in range(len(main)-1) if main[i+1] - main[i] == 1)
        consec_counts[consecs] += 1
    
    total = len(draws)
    pct_0_1 = sum(consec_counts[c] for c in [0, 1]) / total * 100
    
    print(f"  {name}: {pct_0_1:.1f}% have 0-1 consecutives")
    for c in sorted(consec_counts.keys()):
        print(f"    {c} consecutive pairs: {consec_counts[c]} ({consec_counts[c]/total*100:.1f}%)")

# Verify repeat rate claim
print("\n--- VERIFYING REPEAT RATE CLAIM ---")
for lot, name in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        draws = json.load(f)['draws']
    
    repeats = 0
    repeat_counts = Counter()  # How many numbers repeat
    for i in range(len(draws) - 1):
        current = set(draws[i]['main'])
        prev = set(draws[i+1]['main'])
        num_repeats = len(current & prev)
        if num_repeats > 0:
            repeats += 1
        repeat_counts[num_repeats] += 1
    
    repeat_rate = repeats / (len(draws)-1) * 100
    print(f"  {name}: {repeat_rate:.1f}% of draws have at least 1 repeat")
    print(f"    Distribution: {dict(repeat_counts)}")
    
    # Average repeats when there is a repeat
    total_repeats = sum(k * v for k, v in repeat_counts.items() if k > 0)
    draws_with_repeats = sum(v for k, v in repeat_counts.items() if k > 0)
    if draws_with_repeats > 0:
        avg_repeats = total_repeats / draws_with_repeats
        print(f"    When repeats happen, avg count: {avg_repeats:.2f}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
