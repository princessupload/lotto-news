"""
Critical Lottery Analysis - Calculate true odds and our improvements
"""
import json
from collections import Counter
from math import comb
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'lottery-analyzer'))

DATA_DIR = Path(__file__).parent / 'data'

lotteries = {
    'l4l': {'name': 'Lucky for Life', 'main': 48, 'pick': 5, 'bonus': 18, 'draws_per_week': 7, 'cost': 2},
    'la': {'name': 'Lotto America', 'main': 52, 'pick': 5, 'bonus': 10, 'draws_per_week': 3, 'cost': 1},
    'pb': {'name': 'Powerball', 'main': 69, 'pick': 5, 'bonus': 26, 'draws_per_week': 3, 'cost': 2},
    'mm': {'name': 'Mega Millions', 'main': 70, 'pick': 5, 'bonus': 25, 'draws_per_week': 2, 'cost': 5}
}

print('=' * 70)
print('CRITICAL LOTTERY ANALYSIS')
print('=' * 70)

results = {}

for lot, config in lotteries.items():
    with open(DATA_DIR / f'{lot}.json') as f:
        data = json.load(f)
    draws = data['draws']
    
    # Base odds calculation
    main_combos = comb(config['main'], config['pick'])
    total_odds = main_combos * config['bonus']
    
    # Position-based analysis
    position_freq = [Counter() for _ in range(5)]
    for d in draws:
        main = sorted(d['main'])
        for pos, num in enumerate(main):
            position_freq[pos][num] += 1
    
    # Top 8 numbers per position - what % of draws do they cover?
    top8_coverage = []
    for pos in range(5):
        top8 = [n for n, _ in position_freq[pos].most_common(8)]
        total = sum(position_freq[pos].values())
        coverage = sum(position_freq[pos][n] for n in top8) / total * 100
        top8_coverage.append(coverage)
    
    avg_coverage = sum(top8_coverage) / 5
    
    # If we pick from top 8 per position, our "hit rate" is avg_coverage per position
    # Combined probability = (avg_coverage/100)^5 for all 5 positions
    our_5_match_rate = (avg_coverage / 100) ** 5 * 100
    
    # Constraint analysis
    repeats = sum(1 for i in range(len(draws)-1) if set(draws[i]['main']) & set(draws[i+1]['main']))
    repeat_rate = repeats / (len(draws)-1) * 100
    
    decade_ok = sum(1 for d in draws if 3 <= len(set(n // 10 for n in d['main'])) <= 5)
    decade_pct = decade_ok / len(draws) * 100
    
    no_consec = sum(1 for d in draws if sum(1 for i in range(len(sorted(d['main']))-1) 
                    if sorted(d['main'])[i+1] - sorted(d['main'])[i] == 1) <= 1)
    consec_pct = no_consec / len(draws) * 100
    
    # Bonus ball - top 5 coverage
    bonus_freq = Counter(d.get('bonus') for d in draws if d.get('bonus'))
    top5_bonus = [b for b, _ in bonus_freq.most_common(5)]
    bonus_coverage = sum(bonus_freq[b] for b in top5_bonus) / len(draws) * 100
    
    # Random odds: 1/main_combos * 1/bonus = 1/total_odds
    # Our odds improvement comes from:
    # 1. Position pools cover avg_coverage% per position
    # 2. Constraints are followed by 86-99% of winners
    # 3. Bonus pool covers bonus_coverage% of draws
    
    # Effective improvement = how much more likely our ticket hits
    position_improvement = (avg_coverage / (100 / config['main'] * 8)) ** 5
    bonus_improvement = bonus_coverage / (100 / config['bonus'] * 5)
    constraint_boost = (decade_pct / 100) * (consec_pct / 100)
    
    total_improvement = position_improvement * bonus_improvement * constraint_boost
    effective_odds = total_odds / max(total_improvement, 1)
    
    # Value analysis
    draws_per_year = config['draws_per_week'] * 52
    cost_per_year = draws_per_year * config['cost']
    
    results[lot] = {
        'name': config['name'],
        'base_odds': total_odds,
        'effective_odds': int(effective_odds),
        'improvement': total_improvement,
        'avg_pool_coverage': avg_coverage,
        'bonus_coverage': bonus_coverage,
        'repeat_rate': repeat_rate,
        'decade_pct': decade_pct,
        'consec_pct': consec_pct,
        'draws_per_year': draws_per_year,
        'cost_per_year': cost_per_year,
        'draws_analyzed': len(draws)
    }
    
    print(f"\n{'='*70}")
    print(f"{config['name'].upper()}")
    print(f"{'='*70}")
    print(f"Base Jackpot Odds:     1 in {total_odds:,}")
    print(f"Draws Analyzed:        {len(draws)}")
    print(f"Cost per ticket:       ${config['cost']}")
    print(f"")
    print(f"OUR POOL ANALYSIS:")
    print(f"  Top 8 per position covers: {avg_coverage:.1f}% of historical wins")
    print(f"  Top 5 bonus covers:        {bonus_coverage:.1f}% of historical wins")
    print(f"  Position coverage:         {top8_coverage}")
    print(f"")
    print(f"CONSTRAINT MATCH RATES:")
    print(f"  Decade spread (3-5):       {decade_pct:.1f}% of winners")
    print(f"  Max 1 consecutive:         {consec_pct:.1f}% of winners")
    print(f"  Repeat from last draw:     {repeat_rate:.1f}% of draws")
    print(f"")
    print(f"IMPROVEMENT CALCULATION:")
    print(f"  Position pool boost:       {position_improvement:.1f}x")
    print(f"  Bonus pool boost:          {bonus_improvement:.1f}x")
    print(f"  Constraint alignment:      {constraint_boost:.2f}")
    print(f"  TOTAL IMPROVEMENT:         {total_improvement:.1f}x")
    print(f"")
    print(f"EFFECTIVE ODDS WITH OUR ANALYSIS:")
    print(f"  Random player:             1 in {total_odds:,}")
    print(f"  Using our analysis:        1 in {int(effective_odds):,}")
    print(f"")
    print(f"YEARLY COST: ${cost_per_year:,} ({draws_per_year} draws)")

print("\n" + "=" * 70)
print("RECOMMENDATION RANKING")
print("=" * 70)

# Sort by best value (lowest effective odds relative to cost)
sorted_by_odds = sorted(results.items(), key=lambda x: x[1]['effective_odds'])

print("\nRanked by BEST ODDS with our analysis:\n")
for i, (lot, r) in enumerate(sorted_by_odds, 1):
    print(f"  {i}. {r['name']}")
    print(f"     Effective: 1 in {r['effective_odds']:,} ({r['improvement']:.1f}x better)")
    print(f"     Pool coverage: {r['avg_pool_coverage']:.1f}% | Repeat rate: {r['repeat_rate']:.1f}%")
    print()

print("=" * 70)
print("MULTI-MONTH STRATEGY RECOMMENDATION")
print("=" * 70)

# Find best lottery for consistent play
best_lot = sorted_by_odds[0][0]
best = results[best_lot]

print(f"\n>>> FOCUS ON: {best['name']} <<<")
print(f"")
print(f"WHY:")
print(f"  - Best effective odds: 1 in {best['effective_odds']:,}")
print(f"  - Our analysis improves odds by {best['improvement']:.1f}x")
print(f"  - {best['repeat_rate']:.1f}% repeat rate - include last draw numbers!")
print(f"  - {best['decade_pct']:.1f}% of winners have 3-5 decade spread")
print(f"  - Only ${best['cost_per_year']:,}/year for all draws")
print(f"")
print(f"3-MONTH STRATEGY:")
print(f"  - Use HOLD ticket for stable, long-term optimized play")
print(f"  - Check NEXT DRAW ticket for momentum plays")
print(f"  - Always include 1-2 numbers from previous draw (repeat pattern)")
print(f"  - Verify all tickets pass constraint checks")
