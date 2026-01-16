"""
TIMING ANALYSIS - When do patterns repeat?
Critical analysis to predict WHEN jackpot-winning patterns will occur again.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path
from itertools import combinations
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent / 'data'

lotteries = {
    'l4l': {'name': 'Lucky for Life', 'draws_per_week': 7},
    'la': {'name': 'Lotto America', 'draws_per_week': 3},
    'pb': {'name': 'Powerball', 'draws_per_week': 3},
    'mm': {'name': 'Mega Millions', 'draws_per_week': 2}
}

print("=" * 80)
print("TIMING ANALYSIS - WHEN DO PATTERNS REPEAT?")
print("=" * 80)

for lot, config in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        data = json.load(f)
    draws = data['draws']
    
    print(f"\n{'='*80}")
    print(f"{config['name'].upper()} - TIMING PATTERNS")
    print(f"{'='*80}")
    
    # 1. NUMBER RETURN TIMING - How many draws until a number comes back?
    print(f"\n--- NUMBER RETURN CYCLES ---")
    
    all_numbers = set(n for d in draws for n in d['main'])
    number_gaps = defaultdict(list)
    
    for num in all_numbers:
        last_seen = None
        for i, d in enumerate(draws):
            if num in d['main']:
                if last_seen is not None:
                    gap = last_seen - i  # Gap in draws
                    number_gaps[num].append(gap)
                last_seen = i
    
    # Calculate average gap for each number
    avg_gaps = {}
    for num in sorted(all_numbers):
        gaps = number_gaps[num]
        if gaps:
            avg_gaps[num] = sum(gaps) / len(gaps)
    
    # Overall statistics
    all_gaps = [g for gaps in number_gaps.values() for g in gaps]
    if all_gaps:
        overall_avg = sum(all_gaps) / len(all_gaps)
        print(f"  Average draws between appearances: {overall_avg:.1f}")
        print(f"  Median gap: {sorted(all_gaps)[len(all_gaps)//2]}")
        print(f"  Most common gap: {Counter(all_gaps).most_common(1)[0]}")
        
        # Days calculation
        days_per_draw = 7 / config['draws_per_week']
        print(f"  Average days between appearances: {overall_avg * days_per_draw:.1f} days")
    
    # 2. WHICH NUMBERS ARE OVERDUE RIGHT NOW?
    print(f"\n--- OVERDUE NUMBERS (Due to appear soon) ---")
    
    current_gaps = {}
    for num in all_numbers:
        # Find how many draws since this number appeared
        for i, d in enumerate(draws):
            if num in d['main']:
                current_gaps[num] = i
                break
        else:
            current_gaps[num] = len(draws)
    
    # Find numbers that are overdue (current gap > average gap)
    overdue = []
    for num in all_numbers:
        if num in avg_gaps and num in current_gaps:
            if current_gaps[num] > avg_gaps[num] * 1.3:  # 30% overdue
                overdue.append((num, current_gaps[num], avg_gaps[num]))
    
    overdue.sort(key=lambda x: x[1] / x[2], reverse=True)
    print(f"  Most overdue numbers:")
    for num, curr, avg in overdue[:10]:
        ratio = curr / avg
        print(f"    {num}: {curr} draws since last (avg: {avg:.1f}) - {ratio:.1f}x overdue")
    
    # 3. CONSECUTIVE REPEAT TIMING - When does a number repeat from previous draw?
    print(f"\n--- CONSECUTIVE REPEAT TIMING ---")
    
    repeat_gaps = []  # How many draws between consecutive repeats?
    last_repeat_draw = None
    for i in range(len(draws) - 1):
        curr = set(draws[i]['main'])
        prev = set(draws[i+1]['main'])
        if curr & prev:  # There's a repeat
            if last_repeat_draw is not None:
                repeat_gaps.append(last_repeat_draw - i)
            last_repeat_draw = i
    
    if repeat_gaps:
        avg_repeat_gap = sum(repeat_gaps) / len(repeat_gaps)
        print(f"  Average draws between repeat events: {avg_repeat_gap:.1f}")
        print(f"  Most common gap: {Counter(repeat_gaps).most_common(3)}")
        
        # When is next repeat expected?
        draws_since_last_repeat = None
        for i in range(len(draws) - 1):
            if set(draws[i]['main']) & set(draws[i+1]['main']):
                draws_since_last_repeat = i
                break
        
        if draws_since_last_repeat is not None:
            print(f"  Draws since last repeat: {draws_since_last_repeat}")
            if draws_since_last_repeat > avg_repeat_gap:
                print(f"  STATUS: OVERDUE for a repeat! (expect in next 1-3 draws)")
            else:
                expected = avg_repeat_gap - draws_since_last_repeat
                print(f"  Expected draws until next repeat: {expected:.0f}")
    
    # 4. THREE-COMBO REPEAT TIMING
    print(f"\n--- 3-NUMBER COMBO REPEAT TIMING ---")
    
    combo_appearances = defaultdict(list)
    for i, d in enumerate(draws):
        main = tuple(sorted(d['main']))
        for c3 in combinations(main, 3):
            combo_appearances[c3].append(i)
    
    # Find combos that have repeated and their gaps
    combo_gaps = []
    for combo, apps in combo_appearances.items():
        if len(apps) >= 2:
            for j in range(len(apps) - 1):
                gap = apps[j] - apps[j+1]
                combo_gaps.append(gap)
    
    if combo_gaps:
        avg_combo_gap = sum(combo_gaps) / len(combo_gaps)
        print(f"  Average draws between 3-combo repeats: {avg_combo_gap:.1f}")
        print(f"  Most common gaps: {Counter(combo_gaps).most_common(5)}")
        
        # Find combos that are due to repeat
        print(f"\n  3-Combos most likely to repeat soon:")
        combo_due = []
        for combo, apps in combo_appearances.items():
            if len(apps) >= 2:
                last_app = apps[0]  # Most recent
                avg_gap_for_combo = sum(apps[j] - apps[j+1] for j in range(len(apps)-1)) / (len(apps)-1)
                if last_app > avg_gap_for_combo * 0.7:  # Getting close to due
                    combo_due.append((combo, last_app, avg_gap_for_combo, len(apps)))
        
        combo_due.sort(key=lambda x: x[1] / x[2], reverse=True)
        for combo, last, avg, count in combo_due[:5]:
            print(f"    {list(combo)}: appeared {count}x, last seen {last} draws ago (avg gap: {avg:.0f})")
    
    # 5. POSITION-SPECIFIC REPEAT TIMING
    print(f"\n--- POSITION REPEAT TIMING ---")
    
    for pos in range(5):
        pos_nums = [sorted(d['main'])[pos] for d in draws]
        
        # Find gaps between same-position repeats
        pos_repeat_gaps = []
        for i in range(len(pos_nums) - 1):
            if pos_nums[i] == pos_nums[i+1]:
                # Found a repeat, now find gap to previous repeat
                for j in range(i+1, len(pos_nums) - 1):
                    if pos_nums[j] == pos_nums[j+1]:
                        pos_repeat_gaps.append(j - i)
                        break
        
        if pos_repeat_gaps:
            avg_pos_gap = sum(pos_repeat_gaps) / len(pos_repeat_gaps)
            print(f"  Position {pos+1}: avg {avg_pos_gap:.1f} draws between consecutive repeats")
    
    # 6. BONUS BALL TIMING
    print(f"\n--- BONUS BALL TIMING ---")
    
    bonus_list = [d.get('bonus') for d in draws]
    bonus_gaps = defaultdict(list)
    
    for b in set(bonus_list):
        if b is None:
            continue
        last_seen = None
        for i, bonus in enumerate(bonus_list):
            if bonus == b:
                if last_seen is not None:
                    bonus_gaps[b].append(last_seen - i)
                last_seen = i
    
    # Find overdue bonus balls
    overdue_bonus = []
    for b in set(bonus_list):
        if b is None:
            continue
        gaps = bonus_gaps[b]
        if gaps:
            avg = sum(gaps) / len(gaps)
            curr = next((i for i, x in enumerate(bonus_list) if x == b), len(draws))
            if curr > avg * 1.2:
                overdue_bonus.append((b, curr, avg))
    
    overdue_bonus.sort(key=lambda x: x[1] / x[2], reverse=True)
    print(f"  Most overdue bonus balls:")
    for b, curr, avg in overdue_bonus[:5]:
        print(f"    Bonus {b}: {curr} draws since (avg: {avg:.1f}) - {curr/avg:.1f}x overdue")

print("\n" + "=" * 80)
print("PREDICTIVE RECOMMENDATIONS")
print("=" * 80)

# Generate timing-based predictions
for lot, config in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        draws = json.load(f)['draws']
    
    print(f"\n--- {config['name'].upper()} ---")
    
    # Get last draw
    last_draw = sorted(draws[0]['main'])
    last_bonus = draws[0].get('bonus')
    
    print(f"  Last draw: {last_draw} + Bonus: {last_bonus}")
    
    # Predict based on timing
    # 1. Numbers from last draw likely to repeat (32-45% chance)
    all_numbers = set(n for d in draws for n in d['main'])
    
    # Calculate which last draw numbers have best repeat history
    repeat_candidates = []
    for num in last_draw:
        repeat_count = sum(1 for i in range(min(100, len(draws)-1)) 
                         if num in draws[i]['main'] and num in draws[i+1]['main'])
        repeat_candidates.append((num, repeat_count))
    
    repeat_candidates.sort(key=lambda x: -x[1])
    best_repeats = [n for n, _ in repeat_candidates[:2]]
    
    # 2. Overdue numbers
    current_gaps = {}
    avg_gaps = {}
    for num in all_numbers:
        gaps = []
        last = None
        for i, d in enumerate(draws):
            if num in d['main']:
                if last is not None:
                    gaps.append(last - i)
                last = i
                if current_gaps.get(num) is None:
                    current_gaps[num] = i
        if gaps:
            avg_gaps[num] = sum(gaps) / len(gaps)
    
    overdue = [(n, current_gaps.get(n, 999), avg_gaps.get(n, 50)) 
               for n in all_numbers if n in avg_gaps and n in current_gaps]
    overdue.sort(key=lambda x: x[1] / x[2], reverse=True)
    best_overdue = [n for n, _, _ in overdue[:3]]
    
    print(f"\n  TIMING-BASED PREDICTION:")
    print(f"    Best repeat candidates from last draw: {best_repeats}")
    print(f"    Most overdue numbers: {best_overdue[:5]}")
    
    # Combine for ultimate prediction
    combined = set(best_repeats[:1]) | set(best_overdue[:4])
    print(f"    Combined timing pick: {sorted(combined)}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
