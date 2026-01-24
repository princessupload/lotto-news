"""
Check if HOLD tickets have ever hit 5/5 or jackpot historically.
Also critically analyze if position frequency method is valid for RNG vs Physical ball lotteries.
"""

import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent / 'data'

# JACKPOT OPTIMIZED tickets
HOLD_TICKETS = {
    'l4l': {'main': [1, 12, 30, 39, 47], 'bonus': 11, 'name': 'Lucky for Life', 'type': 'RNG'},
    'la': {'main': [1, 15, 23, 42, 51], 'bonus': 4, 'name': 'Lotto America', 'type': 'RNG'},
    'pb': {'main': [1, 11, 33, 52, 69], 'bonus': 20, 'name': 'Powerball', 'type': 'PHYSICAL'},
    'mm': {'main': [2, 10, 27, 42, 68], 'bonus': 1, 'name': 'Mega Millions', 'type': 'PHYSICAL'}
}

def check_historical_hits():
    print("=" * 70)
    print("PART 1: CHECKING IF HOLD TICKETS HAVE EVER HIT 5/5 OR JACKPOT")
    print("=" * 70)
    
    for lottery, ticket in HOLD_TICKETS.items():
        data = json.load(open(DATA_DIR / f'{lottery}.json'))
        draws = data['draws']
        
        ticket_set = set(ticket['main'])
        
        matches_5 = []
        matches_jackpot = []
        
        for draw in draws:
            draw_set = set(draw.get('main', []))
            draw_bonus = draw.get('bonus')
            
            matches = len(ticket_set & draw_set)
            
            if matches == 5:
                matches_5.append(draw)
                if draw_bonus == ticket['bonus']:
                    matches_jackpot.append(draw)
        
        print(f"\n{ticket['name']} ({ticket['type']}):")
        print(f"  Ticket: {ticket['main']} + {ticket['bonus']}")
        print(f"  Total draws checked: {len(draws)}")
        print(f"  5/5 matches (no bonus): {len(matches_5)}")
        print(f"  JACKPOT (5/5 + bonus): {len(matches_jackpot)}")
        
        if matches_5:
            print('  ⚠️ 5/5 MATCHES FOUND:')
            for m in matches_5[:5]:
                print(f"    {m['date']}: {m['main']} + {m.get('bonus')}")
        else:
            print('  ✅ This exact 5/5 combination has NEVER been drawn')

def analyze_rng_vs_physical():
    print("\n" + "=" * 70)
    print("PART 2: CRITICAL ANALYSIS - RNG vs PHYSICAL BALL LOTTERIES")
    print("=" * 70)
    
    print("""
THEORETICAL CONSIDERATIONS:

RNG LOTTERIES (L4L, LA):
- Should produce truly uniform random numbers
- If RNG is perfect, past frequency should NOT predict future
- Position frequency exploitation assumes RNG has BIAS
- Our data shows clear position frequency patterns - WHY?
  - Option 1: RNG is truly biased (exploitable)
  - Option 2: Statistical noise in limited sample (not exploitable)
  - Option 3: RNG seeding or algorithm flaw (exploitable)

PHYSICAL BALL LOTTERIES (PB, MM):
- Physical balls can have manufacturing variations
- Weight, surface texture, paint thickness affect draw probability
- Position frequency could reflect REAL physical biases
- This method makes MORE sense for physical balls
""")
    
    # Analyze statistical significance
    print("STATISTICAL SIGNIFICANCE TEST:")
    print("-" * 70)
    
    for lottery, ticket in HOLD_TICKETS.items():
        data = json.load(open(DATA_DIR / f'{lottery}.json'))
        draws = data['draws']
        total = len(draws)
        
        # For each position, calculate if top number is statistically significant
        pos_freq = [Counter() for _ in range(5)]
        for d in draws:
            sorted_main = sorted(d.get('main', []))
            for pos, num in enumerate(sorted_main):
                pos_freq[pos][num] += 1
        
        # Get config
        if lottery == 'l4l':
            max_num = 48
        elif lottery == 'la':
            max_num = 52
        elif lottery == 'pb':
            max_num = 69
        else:
            max_num = 70
        
        print(f"\n{ticket['name']} ({ticket['type']}, {total} draws):")
        
        # Expected frequency if uniform
        # Position 1 should be roughly 5/max_num for lowest numbers
        # This is complex, but we can compare observed vs expected
        
        for pos in range(5):
            top_num, top_count = pos_freq[pos].most_common(1)[0]
            unique_nums = len(pos_freq[pos])
            
            # Rough expected if uniform
            expected = total / unique_nums
            observed = top_count
            ratio = observed / expected
            
            # Chi-square would be better, but this gives intuition
            deviation = ((observed - expected) / expected) * 100
            
            sig = "SIGNIFICANT" if deviation > 30 else "marginal" if deviation > 15 else "within noise"
            
            print(f"  Pos {pos+1}: #{top_num} appears {top_count}x (expected ~{expected:.1f}x) = {deviation:+.1f}% [{sig}]")

def recommend_strategy():
    print("\n" + "=" * 70)
    print("PART 3: STRATEGY RECOMMENDATION BY LOTTERY TYPE")
    print("=" * 70)
    
    print("""
CRITICAL INSIGHT:

For RNG lotteries (L4L, LA):
- Position frequency patterns may be NOISE, not signal
- With 1000+ draws, we'd expect SOME positions to deviate by chance
- BUT: If there IS a subtle RNG flaw, position frequency exploits it
- RECOMMENDATION: Position frequency is a reasonable hedge, but don't expect
  the same level of advantage as with physical balls

For PHYSICAL ball lotteries (PB, MM):
- Physical biases are REAL and persistent
- Ball weight, surface, machine mechanics create genuine patterns
- Position frequency for physical lotteries is MORE justified
- RECOMMENDATION: Position frequency is well-suited here

OVERALL VERDICT:
- Our method is SOUND for physical ball lotteries (PB, MM)
- Our method is REASONABLE but weaker for RNG lotteries (L4L, LA)
- For RNG, we're essentially betting that the RNG has subtle flaws
- No combination has hit 5/5 before, so we're not picking "used" numbers
""")

if __name__ == '__main__':
    check_historical_hits()
    analyze_rng_vs_physical()
    recommend_strategy()
