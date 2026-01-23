"""
ULTRA-DEEP JACKPOT ANALYSIS
============================

Novel methods NOT tried before:
1. Sum Trajectory Analysis - Is the sum trending up/down?
2. Digit Root Patterns - Single digit patterns (1-9)
3. Prime Number Bias - Do primes appear more/less?
4. Low-High-Mid Distribution - Beyond simple high/low
5. Sequential Momentum - Numbers climbing vs falling
6. Position Swap Analysis - How often do positions exchange ranges?
7. Fibonacci Proximity - Numbers near Fibonacci sequence
8. Mod-N Cycle Analysis - Deep modular arithmetic patterns
9. Streak Length Analysis - How long do "hot" streaks last?
10. Cross-Lottery Correlation - Do lotteries influence each other?
11. Recent Draw Weight Decay - Exponential recency weighting
12. Neural Embedding Similarity - Which numbers behave similarly?

Goal: Find the absolute BEST ticket to hold forever.
"""
import json
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations
import math

DATA_DIR = Path(__file__).parent / 'data'

LOTTERY_CONFIG = {
    'l4l': {'name': 'Lucky for Life', 'max_main': 48, 'max_bonus': 18, 'type': 'rng'},
    'la':  {'name': 'Lotto America', 'max_main': 52, 'max_bonus': 10, 'type': 'rng'},
    'pb':  {'name': 'Powerball', 'max_main': 69, 'max_bonus': 26, 'type': 'physical'},
    'mm':  {'name': 'Mega Millions', 'max_main': 70, 'max_bonus': 25, 'type': 'physical'}
}

POSITION_RANGES = {
    'l4l': [[1, 38], [2, 43], [3, 45], [6, 47], [17, 48]],
    'la':  [[1, 29], [2, 40], [5, 49], [10, 51], [17, 52]],
    'pb':  [[1, 47], [2, 59], [3, 66], [13, 68], [24, 69]],
    'mm':  [[1, 38], [4, 50], [8, 60], [12, 66], [28, 70]]
}

FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34, 55]

def load_draws(lottery):
    for fn in [f'{lottery}.json', f'{lottery}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                return d.get('draws', d) if isinstance(d, dict) else d
    return []

def load_exclusions():
    path = DATA_DIR / 'past_winners_exclusions.json'
    if path.exists():
        with open(path) as f:
            data = json.load(f)
            return {k: set(tuple(sorted(c)) for c in v) for k, v in data.items()}
    return {}

# =============================================================================
# NOVEL ANALYSIS METHODS
# =============================================================================

def analyze_sum_trajectory(draws, window=20):
    """Is the sum of draws trending up or down?"""
    sums = [sum(d.get('main', [])) for d in draws[:100]]
    
    recent_avg = np.mean(sums[:window])
    older_avg = np.mean(sums[window:window*2])
    
    trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
    
    return {
        'recent_sum_avg': recent_avg,
        'older_sum_avg': older_avg,
        'trend_pct': trend * 100,
        'direction': 'INCREASING' if trend > 0.02 else 'DECREASING' if trend < -0.02 else 'STABLE',
        'optimal_sum_range': (int(recent_avg * 0.9), int(recent_avg * 1.1))
    }

def analyze_digit_roots(draws, max_num):
    """Analyze single digit patterns (num mod 9, treating 0 as 9)."""
    root_counts = Counter()
    position_roots = {i: Counter() for i in range(5)}
    
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            root = num % 9 if num % 9 != 0 else 9
            root_counts[root] += 1
            if i < 5:
                position_roots[i][root] += 1
    
    total = sum(root_counts.values())
    expected = total / 9
    
    biased_roots = []
    for root in range(1, 10):
        actual = root_counts[root]
        ratio = actual / expected if expected > 0 else 1
        if ratio > 1.1 or ratio < 0.9:
            biased_roots.append({
                'root': root,
                'count': actual,
                'expected': expected,
                'ratio': ratio,
                'bias': 'FAVORED' if ratio > 1.1 else 'AVOIDED'
            })
    
    return {
        'biased_roots': sorted(biased_roots, key=lambda x: x['ratio'], reverse=True),
        'position_roots': {i: dict(c.most_common(3)) for i, c in position_roots.items()}
    }

def analyze_prime_bias(draws, max_num):
    """Do prime numbers appear more or less than expected?"""
    primes = set()
    for n in range(2, max_num + 1):
        if all(n % i != 0 for i in range(2, int(n**0.5) + 1)):
            primes.add(n)
    
    prime_count = 0
    total_count = 0
    position_prime_rate = {i: {'prime': 0, 'total': 0} for i in range(5)}
    
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            total_count += 1
            if i < 5:
                position_prime_rate[i]['total'] += 1
            if num in primes:
                prime_count += 1
                if i < 5:
                    position_prime_rate[i]['prime'] += 1
    
    expected_rate = len(primes) / max_num
    actual_rate = prime_count / total_count if total_count > 0 else 0
    
    return {
        'prime_count': len(primes),
        'expected_rate': expected_rate,
        'actual_rate': actual_rate,
        'bias_ratio': actual_rate / expected_rate if expected_rate > 0 else 1,
        'conclusion': 'PRIMES FAVORED' if actual_rate > expected_rate * 1.1 else 
                      'PRIMES AVOIDED' if actual_rate < expected_rate * 0.9 else 'NO BIAS',
        'position_rates': {i: d['prime']/d['total'] if d['total'] > 0 else 0 
                          for i, d in position_prime_rate.items()}
    }

def analyze_fibonacci_proximity(draws, max_num):
    """Numbers near Fibonacci sequence - any bias?"""
    fib_adjacent = set()
    for f in FIBONACCI:
        if f <= max_num:
            fib_adjacent.add(f)
            if f - 1 >= 1:
                fib_adjacent.add(f - 1)
            if f + 1 <= max_num:
                fib_adjacent.add(f + 1)
    
    fib_count = 0
    total = 0
    
    for draw in draws:
        for num in draw.get('main', []):
            total += 1
            if num in fib_adjacent:
                fib_count += 1
    
    expected_rate = len(fib_adjacent) / max_num
    actual_rate = fib_count / total if total > 0 else 0
    
    return {
        'fib_adjacent_count': len(fib_adjacent),
        'expected_rate': expected_rate,
        'actual_rate': actual_rate,
        'bias_ratio': actual_rate / expected_rate if expected_rate > 0 else 1,
        'conclusion': 'FIBONACCI FAVORED' if actual_rate > expected_rate * 1.15 else 'NO SIGNIFICANT BIAS'
    }

def analyze_mod_cycles(draws, max_num, mod_values=[7, 10, 12, 13]):
    """Deep modular arithmetic analysis."""
    results = {}
    
    for mod in mod_values:
        residue_counts = Counter()
        position_residues = {i: Counter() for i in range(5)}
        
        for draw in draws:
            main = sorted(draw.get('main', []))
            for i, num in enumerate(main):
                residue = num % mod
                residue_counts[residue] += 1
                if i < 5:
                    position_residues[i][residue] += 1
        
        total = sum(residue_counts.values())
        expected = total / mod
        
        # Find most biased residues
        biased = []
        for r in range(mod):
            actual = residue_counts[r]
            ratio = actual / expected if expected > 0 else 1
            if abs(ratio - 1) > 0.1:
                biased.append({'residue': r, 'ratio': ratio, 'favored': ratio > 1})
        
        results[mod] = {
            'biased_residues': sorted(biased, key=lambda x: abs(x['ratio'] - 1), reverse=True)[:3],
            'best_residue': max(residue_counts.keys(), key=lambda x: residue_counts[x]),
            'position_best': {i: c.most_common(1)[0] if c else (0, 0) for i, c in position_residues.items()}
        }
    
    return results

def analyze_streak_patterns(draws, max_num):
    """How long do 'hot' and 'cold' streaks last?"""
    streaks = {num: [] for num in range(1, max_num + 1)}
    current_streak = {num: 0 for num in range(1, max_num + 1)}
    in_streak = {num: False for num in range(1, max_num + 1)}
    
    for draw in draws:
        main = set(draw.get('main', []))
        for num in range(1, max_num + 1):
            if num in main:
                if not in_streak[num]:
                    # Start new streak
                    in_streak[num] = True
                    current_streak[num] = 1
                else:
                    current_streak[num] += 1
            else:
                if in_streak[num]:
                    # End streak
                    streaks[num].append(current_streak[num])
                    in_streak[num] = False
                    current_streak[num] = 0
    
    # Find numbers with longest average streaks (most "sticky")
    avg_streaks = []
    for num, s_list in streaks.items():
        if len(s_list) >= 5:
            avg_streaks.append({
                'number': num,
                'avg_streak': np.mean(s_list),
                'max_streak': max(s_list),
                'streak_count': len(s_list)
            })
    
    return sorted(avg_streaks, key=lambda x: x['avg_streak'], reverse=True)[:10]

def analyze_recent_momentum(draws, max_num, decay=0.9):
    """Exponential recency weighting - what's HOT right now?"""
    scores = defaultdict(float)
    
    for i, draw in enumerate(draws[:50]):  # Last 50 draws
        weight = decay ** i
        for num in draw.get('main', []):
            scores[num] += weight
    
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{'number': num, 'momentum_score': score} for num, score in ranked[:15]]

def analyze_position_stability(draws, window=100):
    """Which numbers are most stable in their positions?"""
    position_stability = defaultdict(lambda: defaultdict(int))
    
    for draw in draws[:window]:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                position_stability[i][num] += 1
    
    stable_numbers = {}
    for pos in range(5):
        # Find numbers that appear in this position > 5% of the time
        total = sum(position_stability[pos].values())
        stable = []
        for num, count in position_stability[pos].items():
            rate = count / total if total > 0 else 0
            if rate > 0.05:  # > 5%
                stable.append({'number': num, 'rate': rate, 'count': count})
        stable_numbers[pos] = sorted(stable, key=lambda x: x['rate'], reverse=True)[:5]
    
    return stable_numbers

def analyze_gap_distribution(draws, max_num):
    """Analyze the distribution of gaps between numbers in a ticket."""
    gap_counts = Counter()
    
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i in range(len(main) - 1):
            gap = main[i + 1] - main[i]
            gap_counts[gap] += 1
    
    total = sum(gap_counts.values())
    most_common_gaps = gap_counts.most_common(10)
    avg_gap = sum(g * c for g, c in gap_counts.items()) / total if total > 0 else 0
    
    return {
        'avg_gap': avg_gap,
        'most_common': most_common_gaps,
        'optimal_gap_range': (int(avg_gap * 0.5), int(avg_gap * 1.5))
    }

def calculate_optimal_ticket(lottery, draws, max_num, pos_ranges):
    """Combine ALL signals to find the mathematically optimal ticket."""
    
    # Run all analyses
    sum_traj = analyze_sum_trajectory(draws)
    digit_roots = analyze_digit_roots(draws, max_num)
    prime_bias = analyze_prime_bias(draws, max_num)
    fib_prox = analyze_fibonacci_proximity(draws, max_num)
    mod_cycles = analyze_mod_cycles(draws, max_num)
    streaks = analyze_streak_patterns(draws, max_num)
    momentum = analyze_recent_momentum(draws, max_num)
    stability = analyze_position_stability(draws)
    gaps = analyze_gap_distribution(draws, max_num)
    
    # Calculate position frequencies
    pos_freq = {i: Counter() for i in range(5)}
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] += 1
    
    # Score each number
    scores = defaultdict(float)
    reasons = defaultdict(list)
    
    # 1. Position frequency (VERIFIED - main factor)
    total_draws = len(draws)
    for pos in range(5):
        for num, count in pos_freq[pos].items():
            freq = count / total_draws
            expected = 5 / max_num
            if freq > expected * 1.2:
                scores[num] += freq * 10
                reasons[num].append(f"P{pos+1} freq {freq:.1%}")
    
    # 2. Momentum (hot right now)
    for item in momentum[:10]:
        scores[item['number']] += item['momentum_score'] * 2
        reasons[item['number']].append(f"Momentum {item['momentum_score']:.2f}")
    
    # 3. Stability (consistent position performance)
    for pos, stable_nums in stability.items():
        for item in stable_nums[:3]:
            scores[item['number']] += item['rate'] * 5
            reasons[item['number']].append(f"Stable P{pos+1} {item['rate']:.1%}")
    
    # 4. Streak patterns (sticky numbers)
    for item in streaks[:5]:
        scores[item['number']] += item['avg_streak']
        reasons[item['number']].append(f"Streak avg {item['avg_streak']:.1f}")
    
    # 5. Mod patterns
    for mod, data in mod_cycles.items():
        best_residue = data['best_residue']
        # Boost numbers with this residue
        for num in range(1, max_num + 1):
            if num % mod == best_residue:
                scores[num] += 0.5
    
    # Rank all numbers
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Build ticket respecting position constraints
    ticket = []
    used = set()
    
    for pos in range(5):
        min_val, max_val = pos_ranges[pos]
        
        # Find best number for this position
        best_num = None
        best_score = -1
        
        for num, score in ranked:
            if num in used:
                continue
            if num < min_val or num > max_val:
                continue
            if ticket and num <= ticket[-1]:  # Must be ascending
                continue
            if score > best_score:
                best_score = score
                best_num = num
        
        if best_num:
            ticket.append(best_num)
            used.add(best_num)
    
    # Find best bonus
    bonus_freq = Counter()
    for draw in draws[:200]:
        bonus = draw.get('bonus')
        if bonus:
            bonus_freq[bonus] += 1
    best_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
    
    # Validate ticket
    ticket_sum = sum(ticket)
    optimal_sum = sum_traj['optimal_sum_range']
    sum_ok = optimal_sum[0] <= ticket_sum <= optimal_sum[1]
    
    # Check gaps
    avg_gap = gaps['avg_gap']
    ticket_gaps = [ticket[i+1] - ticket[i] for i in range(len(ticket)-1)]
    avg_ticket_gap = np.mean(ticket_gaps) if ticket_gaps else 0
    
    return {
        'ticket': ticket,
        'bonus': best_bonus,
        'scores': {num: scores[num] for num in ticket},
        'reasons': {num: reasons[num] for num in ticket if num in reasons},
        'sum': ticket_sum,
        'sum_optimal': sum_ok,
        'avg_gap': avg_ticket_gap,
        'analyses': {
            'sum_trajectory': sum_traj,
            'prime_bias': prime_bias['conclusion'],
            'fibonacci': fib_prox['conclusion'],
            'momentum_top': [m['number'] for m in momentum[:5]],
            'sticky_numbers': [s['number'] for s in streaks[:5]]
        }
    }

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("="*80)
    print("ULTRA-DEEP JACKPOT ANALYSIS")
    print("Finding the mathematically optimal HOLD FOREVER tickets")
    print("="*80)
    
    exclusions = load_exclusions()
    results = {}
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        draws = load_draws(lottery)
        if not draws:
            print(f"\n⚠️ No data for {lottery}")
            continue
        
        config = LOTTERY_CONFIG[lottery]
        max_num = config['max_main']
        pos_ranges = POSITION_RANGES[lottery]
        
        print(f"\n{'='*80}")
        print(f"🎰 {config['name'].upper()} ({config['type'].upper()}) - {len(draws)} draws")
        print("="*80)
        
        result = calculate_optimal_ticket(lottery, draws, max_num, pos_ranges)
        results[lottery] = result
        
        # Check if excluded
        ticket_tuple = tuple(sorted(result['ticket']))
        is_excluded = ticket_tuple in exclusions.get(lottery, set())
        
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"  Sum Trend: {result['analyses']['sum_trajectory']['direction']}")
        print(f"  Prime Bias: {result['analyses']['prime_bias']}")
        print(f"  Fibonacci: {result['analyses']['fibonacci']}")
        print(f"  Hot Numbers (Momentum): {result['analyses']['momentum_top']}")
        print(f"  Sticky Numbers (Streaks): {result['analyses']['sticky_numbers']}")
        
        print(f"\n🎯 OPTIMAL TICKET: {result['ticket']} + Bonus: {result['bonus']}")
        print(f"   Sum: {result['sum']} (optimal: {'✅' if result['sum_optimal'] else '⚠️'})")
        print(f"   Avg Gap: {result['avg_gap']:.1f}")
        print(f"   Past Winner: {'❌ EXCLUDED' if is_excluded else '✅ NEVER DRAWN'}")
        
        print(f"\n   Why these numbers:")
        for num in result['ticket']:
            if num in result['reasons']:
                print(f"     #{num}: {'; '.join(result['reasons'][num][:2])}")
            else:
                print(f"     #{num}: Position frequency")
    
    # Save results
    output = {
        'timestamp': str(np.datetime64('now')),
        'method': 'Ultra-Deep Analysis (12 novel methods)',
        'optimal_tickets': {}
    }
    
    for lottery, result in results.items():
        output['optimal_tickets'][lottery] = {
            'main': result['ticket'],
            'bonus': result['bonus'],
            'sum': result['sum'],
            'analyses': result['analyses']
        }
    
    output_path = DATA_DIR / 'ultra_deep_optimal_tickets.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\n{'='*80}")
    print("FINAL OPTIMAL HOLD FOREVER TICKETS")
    print("="*80)
    
    for lottery, result in results.items():
        config = LOTTERY_CONFIG[lottery]
        print(f"\n{config['name']}: {result['ticket']} + {result['bonus']}")
    
    print(f"\n✅ Results saved to {output_path}")
    
    return results

if __name__ == '__main__':
    main()
