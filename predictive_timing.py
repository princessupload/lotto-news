"""
PREDICTIVE TIMING MODEL
When will patterns repeat? Critical analysis for future jackpot prediction.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path
from itertools import combinations
from datetime import datetime

DATA_DIR = Path(__file__).parent / 'data'

lotteries = {
    'l4l': {'name': 'Lucky for Life', 'draws_per_week': 7, 'optimal_window': 400},
    'la': {'name': 'Lotto America', 'draws_per_week': 3, 'optimal_window': 150},
    'pb': {'name': 'Powerball', 'draws_per_week': 3, 'optimal_window': 100},
    'mm': {'name': 'Mega Millions', 'draws_per_week': 2, 'optimal_window': 30}
}

print("=" * 80)
print("PREDICTIVE TIMING MODEL - WHEN WILL PATTERNS REPEAT?")
print("=" * 80)

all_predictions = {}

for lot, config in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        data = json.load(f)
    draws = data['draws']
    
    print(f"\n{'='*80}")
    print(f"{config['name'].upper()}")
    print(f"{'='*80}")
    
    last_draw = sorted(draws[0]['main'])
    last_bonus = draws[0].get('bonus')
    print(f"Last draw: {last_draw} + Bonus: {last_bonus}")
    
    # ========== 1. NUMBER RETURN CYCLES ==========
    print(f"\n--- NUMBER RETURN CYCLES ---")
    
    all_numbers = set(n for d in draws for n in d['main'])
    
    # Calculate gaps correctly (draws since last appearance)
    number_gaps = defaultdict(list)
    for num in all_numbers:
        appearances = [i for i, d in enumerate(draws) if num in d['main']]
        for j in range(len(appearances) - 1):
            gap = appearances[j+1] - appearances[j]
            number_gaps[num].append(gap)
    
    # Current gap (how long since each number appeared)
    current_gaps = {}
    for num in all_numbers:
        for i, d in enumerate(draws):
            if num in d['main']:
                current_gaps[num] = i
                break
        else:
            current_gaps[num] = len(draws)
    
    # Average gap per number
    avg_gaps = {n: sum(g)/len(g) for n, g in number_gaps.items() if g}
    
    # Overall stats
    all_gap_values = [g for gaps in number_gaps.values() for g in gaps]
    if all_gap_values:
        overall_avg = sum(all_gap_values) / len(all_gap_values)
        days_per_draw = 7 / config['draws_per_week']
        print(f"  Avg draws between number appearances: {overall_avg:.1f} ({overall_avg * days_per_draw:.0f} days)")
    
    # ========== 2. OVERDUE NUMBERS ==========
    print(f"\n--- OVERDUE NUMBERS (Expect soon!) ---")
    
    overdue = []
    for num in all_numbers:
        if num in avg_gaps and num in current_gaps:
            ratio = current_gaps[num] / avg_gaps[num] if avg_gaps[num] > 0 else 0
            if ratio > 1.2:  # 20%+ overdue
                overdue.append((num, current_gaps[num], avg_gaps[num], ratio))
    
    overdue.sort(key=lambda x: x[3], reverse=True)
    print(f"  Top 10 overdue numbers:")
    for num, curr, avg, ratio in overdue[:10]:
        status = "VERY OVERDUE!" if ratio > 2 else "Overdue" if ratio > 1.5 else "Due soon"
        print(f"    {num}: {curr} draws since (avg {avg:.0f}) - {ratio:.1f}x [{status}]")
    
    overdue_nums = [n for n, _, _, _ in overdue[:10]]
    
    # ========== 3. REPEAT TIMING ==========
    print(f"\n--- CONSECUTIVE REPEAT PATTERNS ---")
    
    # When do consecutive repeats happen?
    repeat_events = []
    for i in range(len(draws) - 1):
        curr = set(draws[i]['main'])
        prev = set(draws[i+1]['main'])
        overlap = curr & prev
        if overlap:
            repeat_events.append((i, list(overlap)))
    
    if repeat_events:
        # Gap between repeat events
        repeat_gaps = [repeat_events[i+1][0] - repeat_events[i][0] 
                      for i in range(len(repeat_events)-1)]
        
        avg_repeat_gap = sum(repeat_gaps) / len(repeat_gaps) if repeat_gaps else 2
        draws_since_repeat = repeat_events[0][0] if repeat_events else 0
        
        print(f"  Total repeat events: {len(repeat_events)} out of {len(draws)-1} draws")
        print(f"  Repeat rate: {len(repeat_events)/(len(draws)-1)*100:.1f}%")
        print(f"  Avg draws between repeat events: {avg_repeat_gap:.1f}")
        print(f"  Draws since last repeat: {draws_since_repeat}")
        
        if draws_since_repeat >= avg_repeat_gap:
            print(f"  >> REPEAT EXPECTED IN NEXT 1-2 DRAWS! <<")
            expect_repeat = True
        else:
            remaining = avg_repeat_gap - draws_since_repeat
            print(f"  Expected draws until next repeat: ~{remaining:.0f}")
            expect_repeat = draws_since_repeat >= avg_repeat_gap * 0.7
    
    # ========== 4. BEST REPEAT CANDIDATES ==========
    print(f"\n--- BEST REPEAT CANDIDATES FROM LAST DRAW ---")
    
    # Which numbers from last draw have best repeat history?
    repeat_scores = []
    for num in last_draw:
        # Count how often this number repeated consecutively
        repeats = sum(1 for i in range(len(draws)-1) 
                     if num in draws[i]['main'] and num in draws[i+1]['main'])
        total_apps = sum(1 for d in draws if num in d['main'])
        repeat_rate = repeats / total_apps if total_apps > 0 else 0
        repeat_scores.append((num, repeats, repeat_rate))
    
    repeat_scores.sort(key=lambda x: x[1], reverse=True)
    print(f"  Last draw numbers ranked by repeat tendency:")
    for num, count, rate in repeat_scores:
        print(f"    {num}: repeated {count}x ({rate*100:.0f}% of appearances)")
    
    best_repeat_candidates = [n for n, _, _ in repeat_scores[:2]]
    
    # ========== 5. 3-COMBO TIMING ==========
    print(f"\n--- 3-NUMBER COMBO PREDICTIONS ---")
    
    combo_apps = defaultdict(list)
    for i, d in enumerate(draws):
        main = tuple(sorted(d['main']))
        for c3 in combinations(main, 3):
            combo_apps[c3].append(i)
    
    # Find combos that have repeated and calculate when they might repeat again
    combo_predictions = []
    for combo, apps in combo_apps.items():
        if len(apps) >= 2:
            gaps = [apps[j+1] - apps[j] for j in range(len(apps)-1)]
            avg_gap = sum(gaps) / len(gaps)
            last_seen = apps[0]
            expected_return = avg_gap - last_seen
            combo_predictions.append((combo, len(apps), last_seen, avg_gap, expected_return))
    
    # Sort by expected to return soon
    combo_predictions.sort(key=lambda x: x[4])
    
    print(f"  3-Combos expected to repeat soon:")
    for combo, count, last, avg, expected in combo_predictions[:5]:
        if expected <= 20:
            print(f"    {list(combo)}: {count}x total, last {last} draws ago, expect in ~{max(0,expected):.0f} draws")
    
    due_combos = [c for c, _, _, _, e in combo_predictions[:10] if e <= 30]
    
    # ========== 6. POSITION-SPECIFIC PREDICTIONS ==========
    print(f"\n--- POSITION-SPECIFIC TIMING ---")
    
    position_predictions = []
    for pos in range(5):
        pos_nums = [sorted(d['main'])[pos] for d in draws]
        last_num = pos_nums[0]
        
        # When did this number last appear in this position?
        same_pos_apps = [i for i, n in enumerate(pos_nums) if n == last_num]
        if len(same_pos_apps) >= 2:
            gaps = [same_pos_apps[j+1] - same_pos_apps[j] for j in range(len(same_pos_apps)-1)]
            avg_gap = sum(gaps) / len(gaps)
            print(f"  Pos {pos+1}: {last_num} appears every ~{avg_gap:.0f} draws in this position")
        
        # What number is most likely for this position next?
        pos_freq = Counter(pos_nums[:config['optimal_window']])
        top_3 = pos_freq.most_common(3)
        position_predictions.append([n for n, _ in top_3])
    
    # ========== 7. BONUS PREDICTION ==========
    print(f"\n--- BONUS BALL TIMING ---")
    
    bonus_list = [d.get('bonus') for d in draws if d.get('bonus')]
    bonus_gaps = defaultdict(list)
    
    for b in set(bonus_list):
        apps = [i for i, x in enumerate(bonus_list) if x == b]
        for j in range(len(apps) - 1):
            bonus_gaps[b].append(apps[j+1] - apps[j])
    
    bonus_avg = {b: sum(g)/len(g) for b, g in bonus_gaps.items() if g}
    bonus_current = {b: next((i for i, x in enumerate(bonus_list) if x == b), 999) 
                    for b in set(bonus_list) if b}
    
    # Find overdue bonus
    overdue_bonus = []
    for b in bonus_avg:
        if b in bonus_current:
            ratio = bonus_current[b] / bonus_avg[b] if bonus_avg[b] > 0 else 0
            if ratio > 1.0:
                overdue_bonus.append((b, bonus_current[b], bonus_avg[b], ratio))
    
    overdue_bonus.sort(key=lambda x: x[3], reverse=True)
    if overdue_bonus:
        print(f"  Overdue bonus balls:")
        for b, curr, avg, ratio in overdue_bonus[:5]:
            print(f"    Bonus {b}: {curr} draws since (avg {avg:.0f}) - {ratio:.1f}x overdue")
    
    # Should last bonus repeat? (check lottery-specific rate)
    bonus_repeat_apps = sum(1 for i in range(len(bonus_list)-1) if bonus_list[i] == bonus_list[i+1])
    bonus_repeat_rate = bonus_repeat_apps / (len(bonus_list)-1) * 100
    print(f"  Bonus repeat rate: {bonus_repeat_rate:.1f}%")
    
    # ========== BUILD PREDICTION ==========
    print(f"\n{'='*60}")
    print(f"PREDICTION FOR {config['name'].upper()}")
    print(f"{'='*60}")
    
    # Combine all signals
    prediction_pool = set()
    
    # Add best repeat candidates from last draw
    prediction_pool.update(best_repeat_candidates[:2])
    
    # Add overdue numbers
    prediction_pool.update(overdue_nums[:3])
    
    # Add numbers from due 3-combos
    for combo in due_combos[:2]:
        for n in combo:
            prediction_pool.add(n)
    
    # Filter to 5 numbers maintaining position validity
    final_pred = sorted(list(prediction_pool))[:5]
    
    # Ensure we have 5 numbers
    while len(final_pred) < 5:
        for n in overdue_nums:
            if n not in final_pred:
                final_pred.append(n)
                break
    
    final_pred = sorted(final_pred[:5])
    
    # Best bonus prediction
    if overdue_bonus:
        pred_bonus = overdue_bonus[0][0]
    elif bonus_repeat_rate > 5:
        pred_bonus = last_bonus
    else:
        pred_bonus = Counter(bonus_list[:30]).most_common(1)[0][0]
    
    print(f"\n  TIMING-OPTIMIZED TICKET:")
    print(f"  Main: {final_pred}")
    print(f"  Bonus: {pred_bonus}")
    print(f"\n  REASONING:")
    print(f"    - Repeat candidates: {best_repeat_candidates}")
    print(f"    - Overdue numbers: {overdue_nums[:5]}")
    print(f"    - Due 3-combos include: {[list(c) for c in due_combos[:2]]}")
    
    all_predictions[lot] = {
        'main': final_pred,
        'bonus': pred_bonus,
        'repeat_candidates': best_repeat_candidates,
        'overdue': overdue_nums[:5],
        'due_combos': [list(c) for c in due_combos[:3]]
    }

print("\n" + "=" * 80)
print("CRITICAL THINKING: BEST STRATEGY FOR EACH LOTTERY")
print("=" * 80)

print("""
WHAT WE KNOW FOR CERTAIN:
1. NO exact jackpot has EVER repeated in any lottery
2. 32-45% of draws have at least ONE number repeat from previous draw
3. 3-number combos DO repeat (L4L: 2,175 combos, some 7 times!)
4. Position 1 & 5 have 2x higher repeat rates than middle positions
5. Each lottery has an optimal analysis window (L4L:400, LA:150, PB:100, MM:30)

TIMING PATTERNS:
- Repeat events happen every 2-3 draws on average
- Numbers return to same position every 15-50 draws depending on lottery
- 3-combos that have repeated tend to repeat again within 50-150 draws

BEST PREDICTION STRATEGY:
1. Include 1-2 numbers from last draw (highest repeat history)
2. Include 2-3 overdue numbers (due to return)
3. Favor numbers that appear in historically repeating 3-combos
4. Weight positions 1 & 5 repeats higher
5. Use lottery-specific optimal window for frequency analysis

FOR MULTI-MONTH PLAY:
- HOLD tickets capture long-term statistical optima
- TIMING tickets (above) capture imminent repeat patterns
- Play BOTH for best coverage
""")

# Save predictions
with open(DATA_DIR / 'timing_predictions.json', 'w') as f:
    json.dump(all_predictions, f, indent=2)

print("\nTiming predictions saved to timing_predictions.json")
