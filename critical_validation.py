"""
CRITICAL VALIDATION OF ALL DISCOVERIES
Are our discoveries statistically valid? What are we missing?
"""
import json
from collections import Counter, defaultdict
from pathlib import Path
from itertools import combinations
from math import comb
import random

DATA_DIR = Path(__file__).parent / 'data'

lotteries = {
    'l4l': {'name': 'Lucky for Life', 'main': 48, 'pick': 5, 'bonus': 18},
    'la': {'name': 'Lotto America', 'main': 52, 'pick': 5, 'bonus': 10},
    'pb': {'name': 'Powerball', 'main': 69, 'pick': 5, 'bonus': 26},
    'mm': {'name': 'Mega Millions', 'main': 70, 'pick': 5, 'bonus': 25}
}

print("=" * 80)
print("CRITICAL VALIDATION OF ALL DISCOVERIES")
print("=" * 80)

# ========== CRITICAL QUESTION 1 ==========
# Are our "patterns" just what we'd expect from random chance?

print("\n" + "=" * 80)
print("QUESTION 1: Are our patterns better than random chance?")
print("=" * 80)

for lot, config in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        draws = json.load(f)['draws']
    
    print(f"\n--- {config['name']} ---")
    
    # Expected repeat rate for RANDOM draws
    # P(at least 1 overlap between two random 5-number draws from N numbers)
    n = config['main']
    # Using inclusion-exclusion: P(overlap) = 1 - P(no overlap)
    # P(no overlap) = C(n-5, 5) / C(n, 5)
    p_no_overlap = comb(n - 5, 5) / comb(n, 5)
    expected_repeat_rate = (1 - p_no_overlap) * 100
    
    # Actual repeat rate
    actual_repeats = sum(1 for i in range(len(draws)-1) 
                        if set(draws[i]['main']) & set(draws[i+1]['main']))
    actual_repeat_rate = actual_repeats / (len(draws)-1) * 100
    
    print(f"  Expected repeat rate (random): {expected_repeat_rate:.1f}%")
    print(f"  Actual repeat rate:            {actual_repeat_rate:.1f}%")
    
    if actual_repeat_rate > expected_repeat_rate * 1.1:
        print(f"  >> DISCOVERY VALIDATED: Actual > Expected by {actual_repeat_rate - expected_repeat_rate:.1f}%")
    else:
        print(f"  >> WARNING: Our repeat rate is close to random expectation!")

# ========== CRITICAL QUESTION 2 ==========
# Do our position pools actually improve odds, or is this an illusion?

print("\n" + "=" * 80)
print("QUESTION 2: Do position pools actually help?")
print("=" * 80)

for lot, config in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        draws = json.load(f)['draws']
    
    print(f"\n--- {config['name']} ---")
    
    # Build position pools (top 8 per position)
    position_freq = [Counter() for _ in range(5)]
    for d in draws:
        main = sorted(d['main'])
        for pos, num in enumerate(main):
            position_freq[pos][num] += 1
    
    pools = [[n for n, _ in freq.most_common(8)] for freq in position_freq]
    
    # Test: How often would our pools have contained the winning numbers?
    # Use last 100 draws as test set, train on rest
    test_draws = draws[:100]
    
    hits_per_position = [0] * 5
    for d in test_draws:
        main = sorted(d['main'])
        for pos, num in enumerate(main):
            if num in pools[pos]:
                hits_per_position[pos] += 1
    
    hit_rates = [h / len(test_draws) * 100 for h in hits_per_position]
    avg_hit_rate = sum(hit_rates) / 5
    
    # Expected hit rate if random (8 out of N numbers)
    expected_hit_rate = 8 / config['main'] * 100
    
    print(f"  Pool hit rates per position: {[f'{r:.0f}%' for r in hit_rates]}")
    print(f"  Average pool hit rate:       {avg_hit_rate:.1f}%")
    print(f"  Expected if random:          {expected_hit_rate:.1f}%")
    
    if avg_hit_rate > expected_hit_rate * 1.5:
        print(f"  >> POOLS ARE EFFECTIVE: {avg_hit_rate/expected_hit_rate:.1f}x better than random")
    else:
        print(f"  >> WARNING: Pools may not be as effective as we thought")

# ========== CRITICAL QUESTION 3 ==========
# BACKTEST: Would our predictions have hit in the past?

print("\n" + "=" * 80)
print("QUESTION 3: BACKTEST - Would our method hit historical jackpots?")
print("=" * 80)

for lot, config in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        draws = json.load(f)['draws']
    
    print(f"\n--- {config['name']} ---")
    
    # Simulate: For each draw, use prior draws to predict, check against actual
    hits_0 = 0  # 0 matches
    hits_1 = 0  # 1 match
    hits_2 = 0  # 2 matches
    hits_3 = 0  # 3 matches
    hits_4 = 0  # 4 matches
    hits_5 = 0  # 5 matches (jackpot!)
    
    # Test on last 50 draws
    for test_idx in range(50):
        actual = set(draws[test_idx]['main'])
        
        # Build prediction from prior draws (simple: top per position)
        prior_draws = draws[test_idx + 1:test_idx + 201]  # Use 200 prior
        if len(prior_draws) < 50:
            continue
            
        pos_freq = [Counter() for _ in range(5)]
        for d in prior_draws:
            main = sorted(d['main'])
            for pos, num in enumerate(main):
                pos_freq[pos][num] += 1
        
        # Pick top for each position
        pred = set()
        for pos in range(5):
            for num, _ in pos_freq[pos].most_common(10):
                if num not in pred:
                    pred.add(num)
                    break
        
        matches = len(actual & pred)
        if matches == 0: hits_0 += 1
        elif matches == 1: hits_1 += 1
        elif matches == 2: hits_2 += 1
        elif matches == 3: hits_3 += 1
        elif matches == 4: hits_4 += 1
        elif matches == 5: hits_5 += 1
    
    total = hits_0 + hits_1 + hits_2 + hits_3 + hits_4 + hits_5
    if total > 0:
        print(f"  Backtest results (50 draws):")
        print(f"    0/5: {hits_0} ({hits_0/total*100:.0f}%)")
        print(f"    1/5: {hits_1} ({hits_1/total*100:.0f}%)")
        print(f"    2/5: {hits_2} ({hits_2/total*100:.0f}%)")
        print(f"    3/5: {hits_3} ({hits_3/total*100:.0f}%)")
        print(f"    4/5: {hits_4} ({hits_4/total*100:.0f}%)")
        print(f"    5/5: {hits_5} ({hits_5/total*100:.0f}%)")
        
        # Expected from random
        print(f"\n  Expected 3+/5 from random: ~0.1%")
        actual_3plus = (hits_3 + hits_4 + hits_5) / total * 100
        print(f"  Our method 3+/5:           {actual_3plus:.1f}%")
        
        if actual_3plus > 1:
            print(f"  >> METHOD SHOWS IMPROVEMENT!")
        else:
            print(f"  >> Method needs more refinement")

# ========== CRITICAL QUESTION 4 ==========
# What patterns are we MISSING?

print("\n" + "=" * 80)
print("QUESTION 4: What patterns might we be MISSING?")
print("=" * 80)

for lot, config in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        draws = json.load(f)['draws']
    
    print(f"\n--- {config['name']} ---")
    
    # Check: Sum patterns more deeply
    sums = [sum(d['main']) for d in draws]
    sum_diffs = [sums[i] - sums[i+1] for i in range(len(sums)-1)]
    
    # Are sum differences predictable?
    positive_diffs = sum(1 for d in sum_diffs if d > 0)
    print(f"  Sum increases vs decreases: {positive_diffs}/{len(sum_diffs)-positive_diffs}")
    
    # Check: High/low balance
    high_counts = []
    low_counts = []
    mid = config['main'] // 2
    for d in draws:
        highs = sum(1 for n in d['main'] if n > mid)
        high_counts.append(highs)
    
    high_dist = Counter(high_counts)
    print(f"  High number distribution (>{mid}): {dict(sorted(high_dist.items()))}")
    
    # Check: Odd/even beyond just count - patterns in positions
    odd_patterns = Counter()
    for d in draws:
        main = sorted(d['main'])
        pattern = tuple(1 if n % 2 == 1 else 0 for n in main)
        odd_patterns[pattern] += 1
    
    top_odd_patterns = odd_patterns.most_common(5)
    print(f"  Top odd/even patterns (by position):")
    for pattern, count in top_odd_patterns:
        pct = count / len(draws) * 100
        print(f"    {pattern}: {pct:.1f}%")
    
    # Check: Number spacing patterns
    spacings = []
    for d in draws:
        main = sorted(d['main'])
        spacing = tuple(main[i+1] - main[i] for i in range(4))
        spacings.append(spacing)
    
    avg_spacing = [sum(s[i] for s in spacings) / len(spacings) for i in range(4)]
    print(f"  Average spacing between positions: {[f'{s:.1f}' for s in avg_spacing]}")
    
    # Check: Last digit patterns
    last_digits = Counter()
    for d in draws:
        for n in d['main']:
            last_digits[n % 10] += 1
    
    # Are certain last digits overrepresented?
    total_nums = sum(last_digits.values())
    expected = total_nums / 10
    print(f"  Last digit distribution (expected ~{expected:.0f} each):")
    for digit in range(10):
        count = last_digits[digit]
        diff = count - expected
        if abs(diff) > expected * 0.15:
            print(f"    Digit {digit}: {count} ({'+' if diff > 0 else ''}{diff:.0f})")

# ========== CRITICAL QUESTION 5 ==========
# Are our "overdue" numbers actually more likely to appear?

print("\n" + "=" * 80)
print("QUESTION 5: Do 'overdue' numbers actually appear more often?")
print("=" * 80)

for lot, config in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        draws = json.load(f)['draws']
    
    print(f"\n--- {config['name']} ---")
    
    # For each draw, check if "overdue" numbers appeared
    overdue_hit = 0
    overdue_miss = 0
    
    for test_idx in range(100):
        prior = draws[test_idx + 1:test_idx + 200]
        if len(prior) < 100:
            continue
        
        actual = set(draws[test_idx]['main'])
        
        # Find overdue numbers at that point
        all_nums = set(n for d in prior for n in d['main'])
        gaps = {}
        for num in all_nums:
            for i, d in enumerate(prior):
                if num in d['main']:
                    gaps[num] = i
                    break
        
        avg_gap = sum(gaps.values()) / len(gaps) if gaps else 10
        overdue = [n for n, g in gaps.items() if g > avg_gap * 1.5]
        
        # Did any overdue number appear?
        if set(overdue) & actual:
            overdue_hit += 1
        else:
            overdue_miss += 1
    
    total = overdue_hit + overdue_miss
    if total > 0:
        hit_rate = overdue_hit / total * 100
        print(f"  Overdue numbers appeared in: {hit_rate:.1f}% of next draws")
        
        if hit_rate > 40:
            print(f"  >> OVERDUE STRATEGY IS EFFECTIVE!")
        else:
            print(f"  >> Overdue strategy needs refinement")

print("\n" + "=" * 80)
print("CRITICAL GAPS IDENTIFIED")
print("=" * 80)

print("""
POTENTIAL GAPS IN OUR ANALYSIS:

1. GAMBLER'S FALLACY CHECK
   - Are we falling for "overdue = more likely"?
   - Each draw is independent - numbers don't "remember" they're overdue
   - BUT: If patterns exist, they may reflect non-random selection processes

2. HIGH/LOW BALANCE
   - We track decades but not explicit high/low splits
   - Should we add a high/low constraint?

3. LAST DIGIT PATTERNS
   - Some last digits may be over/under-represented
   - Could add last-digit diversity as a constraint

4. NUMBER SPACING
   - Average gaps between consecutive numbers in winning tickets
   - Could validate tickets have "normal" spacing

5. DRAWING MACHINE EFFECTS
   - Are there patterns from specific drawing machines?
   - Date-based patterns (day of week, month)?

6. SAMPLE SIZE CONCERNS
   - MM only has 81 draws - may not be statistically significant
   - LA/PB have 431 - better but still limited

7. OVERFITTING RISK
   - Are we finding patterns that only exist in historical data?
   - Need out-of-sample validation
""")

print("=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)
