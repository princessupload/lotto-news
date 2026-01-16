"""
Find tickets that pass ALL constraints by relaxing spacing slightly
and searching more thoroughly.
"""
import json
from collections import Counter
from pathlib import Path
from itertools import combinations, product
from datetime import datetime

DATA_DIR = Path(__file__).parent / 'data'

LOTTERY_CONFIG = {
    'l4l': {'name': 'Lucky for Life', 'main': 48, 'bonus': 18, 'midpoint': 24, 'spacing': (5, 12)},
    'la': {'name': 'Lotto America', 'main': 52, 'bonus': 10, 'midpoint': 26, 'spacing': (6, 13)},
    'pb': {'name': 'Powerball', 'main': 69, 'bonus': 26, 'midpoint': 35, 'spacing': (8, 18)},
    'mm': {'name': 'Mega Millions', 'main': 70, 'bonus': 25, 'midpoint': 35, 'spacing': (8, 16)}
}

def get_decade(num):
    return num // 10

def count_decades(nums):
    return len(set(get_decade(n) for n in nums))

def count_consecutives(nums):
    sorted_nums = sorted(nums)
    return sum(1 for i in range(len(sorted_nums)-1) if sorted_nums[i+1] - sorted_nums[i] == 1)

def validate(ticket, config, sum_range, optimal_odds):
    sorted_t = sorted(ticket)
    
    # Sum
    if sum(ticket) < sum_range[0] or sum(ticket) > sum_range[1]:
        return False, "sum"
    
    # Decades
    if count_decades(ticket) < 3:
        return False, "decades"
    
    # Consecutives
    if count_consecutives(ticket) > 1:
        return False, "consec"
    
    # High/low
    high = sum(1 for n in ticket if n > config['midpoint'])
    if high < 2 or high > 3:
        return False, "high_low"
    
    # Spacing
    spacings = [sorted_t[i+1] - sorted_t[i] for i in range(4)]
    avg = sum(spacings) / 4
    if avg < config['spacing'][0] or avg > config['spacing'][1]:
        return False, "spacing"
    
    # Odds
    odds = sum(1 for n in ticket if n % 2 == 1)
    if odds not in optimal_odds:
        return False, "odds"
    
    return True, None

results = {}

for lottery, config in LOTTERY_CONFIG.items():
    with open(DATA_DIR / f'{lottery}.json') as f:
        draws = json.load(f)['draws']
    
    print(f"\n{'='*60}")
    print(f"{config['name'].upper()}")
    print(f"{'='*60}")
    
    # Calculate constraints from data
    sums = sorted([sum(d['main']) for d in draws])
    sum_range = (sums[int(len(sums)*0.05)], sums[int(len(sums)*0.95)])
    
    odd_counts = Counter(sum(1 for n in d['main'] if n % 2 == 1) for d in draws)
    optimal_odds = [x[0] for x in odd_counts.most_common(3)]  # Top 3 for flexibility
    
    print(f"Sum range: {sum_range}")
    print(f"Optimal odds: {optimal_odds}")
    
    # Position frequency
    pos_freq = [Counter() for _ in range(5)]
    for d in draws:
        main = sorted(d['main'])
        for pos, num in enumerate(main):
            pos_freq[pos][num] += 1
    
    # 3-combo boost
    combo_counts = Counter()
    for d in draws:
        main = tuple(sorted(d['main']))
        for c3 in combinations(main, 3):
            combo_counts[c3] += 1
    
    combo_boost = Counter()
    for combo, count in combo_counts.items():
        if count >= 2:
            for num in combo:
                combo_boost[num] += count
    
    # Get top candidates per position (more of them)
    position_ranges = []
    for pos in range(5):
        pos_nums = sorted([sorted(d['main'])[pos] for d in draws])
        low = pos_nums[int(len(pos_nums) * 0.02)]
        high = pos_nums[int(len(pos_nums) * 0.98)]
        position_ranges.append((low, high))
    
    position_candidates = []
    for pos in range(5):
        low, high = position_ranges[pos]
        candidates = []
        for num in range(low, high + 1):
            score = pos_freq[pos].get(num, 0) * 10 + combo_boost.get(num, 0)
            candidates.append((num, score))
        candidates.sort(key=lambda x: -x[1])
        position_candidates.append(candidates[:20])
    
    # Search for valid ticket with highest score
    best_ticket = None
    best_score = -1
    
    # Try combinations
    for p1 in position_candidates[0][:8]:
        for p2 in position_candidates[1][:8]:
            if p2[0] <= p1[0]:
                continue
            for p3 in position_candidates[2][:8]:
                if p3[0] <= p2[0]:
                    continue
                for p4 in position_candidates[3][:8]:
                    if p4[0] <= p3[0]:
                        continue
                    for p5 in position_candidates[4][:8]:
                        if p5[0] <= p4[0]:
                            continue
                        
                        ticket = [p1[0], p2[0], p3[0], p4[0], p5[0]]
                        valid, reason = validate(ticket, config, sum_range, optimal_odds)
                        
                        if valid:
                            score = p1[1] + p2[1] + p3[1] + p4[1] + p5[1]
                            if score > best_score:
                                best_score = score
                                best_ticket = ticket
    
    if best_ticket:
        print(f"\nPERFECT TICKET FOUND: {best_ticket}")
        print(f"Score: {best_score}")
        
        # Validate and show
        print(f"\nConstraint check:")
        print(f"  Sum: {sum(best_ticket)} (range: {sum_range})")
        print(f"  Decades: {count_decades(best_ticket)}")
        print(f"  Consecutives: {count_consecutives(best_ticket)}")
        high = sum(1 for n in best_ticket if n > config['midpoint'])
        print(f"  High numbers: {high}")
        spacings = [best_ticket[i+1] - best_ticket[i] for i in range(4)]
        print(f"  Avg spacing: {sum(spacings)/4:.1f}")
        odds = sum(1 for n in best_ticket if n % 2 == 1)
        print(f"  Odd count: {odds}")
        
        # Why these numbers
        print(f"\nWhy each number:")
        for i, num in enumerate(best_ticket):
            rank_list = [n for n, _ in pos_freq[i].most_common(20)]
            rank = rank_list.index(num) + 1 if num in rank_list else "20+"
            freq = pos_freq[i].get(num, 0)
            pct = round(freq / len(draws) * 100, 1)
            combos = combo_boost.get(num, 0)
            print(f"  Pos {i+1}: {num} - #{rank} ({pct}%), in {combos} combos")
        
        # Best bonus
        bonus_freq = Counter(d.get('bonus') for d in draws if d.get('bonus'))
        best_bonus = bonus_freq.most_common(1)[0][0]
        print(f"\nBonus: {best_bonus} (#{1} overall)")
        
        results[lottery] = {
            'name': config['name'],
            'ticket': best_ticket,
            'bonus': best_bonus,
            'score': best_score,
            'sum': sum(best_ticket),
            'decades': count_decades(best_ticket),
            'high_count': high,
            'odd_count': odds,
            'generated': datetime.now().isoformat()
        }
    else:
        print("No perfect ticket found - constraints may be too strict")
        results[lottery] = None

# Save
with open(DATA_DIR / 'perfect_hold_tickets.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 60)
print("YOUR ULTIMATE HOLD TICKETS (ALL CONSTRAINTS PASSED)")
print("=" * 60)

for lot, data in results.items():
    if data:
        print(f"\n{data['name']}:")
        print(f"  {data['ticket']} + Bonus: {data['bonus']}")
        print(f"  Sum: {data['sum']} | Decades: {data['decades']} | High: {data['high_count']} | Odds: {data['odd_count']}")

print("\nSaved to: data/perfect_hold_tickets.json")
