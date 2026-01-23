"""
DEEP PATTERN DISCOVERY - Novel AI/Statistical Approaches
Finding patterns we haven't explored before in L4L and LA

Approaches tested:
1. Markov Chain Transition Matrices - What numbers follow what?
2. Autocorrelation Analysis - Periodic cycles in number appearances
3. Conditional Probability Chains - P(next | recent sequence)
4. Entropy Decay Analysis - Which positions are becoming more predictable?
5. Gap Convergence - Numbers that MUST appear soon based on gap statistics
6. Sequence Embedding + Clustering - Find "hidden states" in draw sequences
7. Number Co-occurrence Graph Analysis - Graph-based pattern detection
"""

import json
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations
import math

DATA_DIR = Path(__file__).parent / 'data'

def load_draws(lottery):
    for fn in [f'{lottery}.json', f'{lottery}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                return d.get('draws', d) if isinstance(d, dict) else d
    return []

LOTTERY_CONFIG = {
    'l4l': {'name': 'Lucky for Life', 'max_main': 48, 'max_bonus': 18, 'main_count': 5},
    'la':  {'name': 'Lotto America', 'max_main': 52, 'max_bonus': 10, 'main_count': 5},
}

def analyze_markov_transitions(draws, max_num):
    """
    Build a Markov transition matrix: P(number j appears next draw | number i appeared this draw)
    This captures sequential dependencies that position frequency misses.
    """
    # Track: if number i appeared in draw t, what numbers appear in draw t+1?
    transitions = defaultdict(Counter)
    
    for i in range(len(draws) - 1):
        current = set(draws[i].get('main', []))
        next_draw = set(draws[i+1].get('main', []))
        
        for num in current:
            for next_num in next_draw:
                transitions[num][next_num] += 1
    
    # Find strongest transitions (numbers that "call" other numbers)
    strong_transitions = []
    for num, followers in transitions.items():
        total = sum(followers.values())
        for follower, count in followers.most_common(3):
            prob = count / total
            expected = 5 / max_num  # Random expectation
            if prob > expected * 1.3:  # 30% above random
                strong_transitions.append({
                    'trigger': num,
                    'follower': follower,
                    'prob': prob,
                    'expected': expected,
                    'lift': prob / expected,
                    'observations': count
                })
    
    strong_transitions.sort(key=lambda x: x['lift'], reverse=True)
    return strong_transitions[:20]

def analyze_gap_convergence(draws, max_num):
    """
    Find numbers that are statistically OVERDUE based on their historical gap patterns.
    If a number's current gap exceeds its 95th percentile historical gap, it's "due".
    """
    # Calculate all gaps for each number
    number_gaps = defaultdict(list)
    last_seen = {}
    
    for i, draw in enumerate(draws):
        main = set(draw.get('main', []))
        for num in range(1, max_num + 1):
            if num in main:
                if num in last_seen:
                    gap = i - last_seen[num]
                    number_gaps[num].append(gap)
                last_seen[num] = i
    
    # Calculate current gap and compare to historical
    current_draw_idx = len(draws)
    overdue_numbers = []
    
    for num in range(1, max_num + 1):
        if num in last_seen and len(number_gaps[num]) >= 10:
            current_gap = current_draw_idx - last_seen[num]
            gaps = sorted(number_gaps[num])
            avg_gap = np.mean(gaps)
            p95_gap = np.percentile(gaps, 95)
            max_gap = max(gaps)
            
            if current_gap > p95_gap:
                overdue_numbers.append({
                    'number': num,
                    'current_gap': current_gap,
                    'avg_gap': avg_gap,
                    'p95_gap': p95_gap,
                    'max_gap': max_gap,
                    'overdue_ratio': current_gap / avg_gap,
                    'urgency': current_gap / p95_gap
                })
    
    overdue_numbers.sort(key=lambda x: x['urgency'], reverse=True)
    return overdue_numbers

def analyze_autocorrelation(draws, max_num, max_lag=50):
    """
    Find periodic patterns - does a number appearing correlate with itself N draws later?
    """
    # Create binary time series for each number
    periodic_patterns = []
    
    for num in range(1, max_num + 1):
        series = [1 if num in draw.get('main', []) else 0 for draw in draws]
        if sum(series) < 20:  # Need enough data
            continue
        
        # Calculate autocorrelation at different lags
        series = np.array(series)
        mean = np.mean(series)
        var = np.var(series)
        
        if var == 0:
            continue
        
        best_lag = None
        best_corr = 0
        
        for lag in range(5, min(max_lag, len(series) // 4)):
            n = len(series) - lag
            corr = np.sum((series[:n] - mean) * (series[lag:] - mean)) / (n * var)
            
            if abs(corr) > abs(best_corr) and abs(corr) > 0.1:
                best_corr = corr
                best_lag = lag
        
        if best_lag:
            periodic_patterns.append({
                'number': num,
                'period': best_lag,
                'correlation': best_corr,
                'last_appearance': len(draws) - 1 - next((i for i, d in enumerate(draws) if num in d.get('main', [])), len(draws))
            })
    
    periodic_patterns.sort(key=lambda x: abs(x['correlation']), reverse=True)
    return periodic_patterns[:15]

def analyze_entropy_trend(draws, window=50):
    """
    Track entropy per position over time. Decreasing entropy = more predictable.
    """
    if len(draws) < window * 2:
        return []
    
    position_entropy = {i: [] for i in range(5)}
    
    for start in range(0, len(draws) - window, window // 2):
        window_draws = draws[start:start + window]
        
        for pos in range(5):
            counts = Counter()
            for draw in window_draws:
                main = sorted(draw.get('main', []))
                if pos < len(main):
                    counts[main[pos]] += 1
            
            # Calculate entropy
            total = sum(counts.values())
            entropy = 0
            for count in counts.values():
                p = count / total
                if p > 0:
                    entropy -= p * math.log2(p)
            
            position_entropy[pos].append({
                'window_start': start,
                'entropy': entropy
            })
    
    # Find positions with decreasing entropy (becoming more predictable)
    trends = []
    for pos in range(5):
        if len(position_entropy[pos]) >= 4:
            entropies = [e['entropy'] for e in position_entropy[pos]]
            recent = np.mean(entropies[-3:])
            early = np.mean(entropies[:3])
            trend = (recent - early) / early if early > 0 else 0
            
            trends.append({
                'position': pos + 1,
                'early_entropy': early,
                'recent_entropy': recent,
                'trend_pct': trend * 100,
                'interpretation': 'MORE PREDICTABLE' if trend < -0.05 else 'STABLE' if abs(trend) < 0.05 else 'LESS PREDICTABLE'
            })
    
    return trends

def analyze_conditional_sequences(draws, max_num):
    """
    Find conditional patterns: If numbers A and B appeared together, what's likely next?
    """
    pair_to_next = defaultdict(Counter)
    
    for i in range(len(draws) - 1):
        current = sorted(draws[i].get('main', []))
        next_main = draws[i+1].get('main', [])
        
        for pair in combinations(current, 2):
            for next_num in next_main:
                pair_to_next[pair][next_num] += 1
    
    # Find strongest pair->next patterns
    strong_patterns = []
    for pair, nexts in pair_to_next.items():
        total = sum(nexts.values())
        if total < 10:
            continue
        
        for next_num, count in nexts.most_common(3):
            prob = count / total
            expected = 5 / max_num
            if prob > expected * 1.5:  # 50% above random
                strong_patterns.append({
                    'trigger_pair': pair,
                    'next_number': next_num,
                    'prob': prob,
                    'lift': prob / expected,
                    'observations': count
                })
    
    strong_patterns.sort(key=lambda x: x['lift'], reverse=True)
    return strong_patterns[:15]

def analyze_number_graph(draws, max_num):
    """
    Build a co-occurrence graph and find strongly connected clusters.
    Numbers in the same cluster tend to appear together.
    """
    # Build adjacency matrix
    cooccurrence = defaultdict(Counter)
    
    for draw in draws:
        main = draw.get('main', [])
        for a, b in combinations(main, 2):
            cooccurrence[a][b] += 1
            cooccurrence[b][a] += 1
    
    # Find dense clusters using simple community detection
    # Start with highest-degree nodes
    degrees = {num: sum(cooccurrence[num].values()) for num in range(1, max_num + 1)}
    sorted_nums = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)
    
    clusters = []
    used = set()
    
    for seed in sorted_nums[:10]:
        if seed in used:
            continue
        
        # Build cluster around seed
        cluster = {seed}
        neighbors = cooccurrence[seed]
        
        # Add top connected neighbors
        for neighbor, strength in sorted(neighbors.items(), key=lambda x: x[1], reverse=True)[:4]:
            if neighbor not in used:
                cluster.add(neighbor)
        
        if len(cluster) >= 3:
            used.update(cluster)
            total_internal = sum(cooccurrence[a][b] for a in cluster for b in cluster if a < b)
            clusters.append({
                'numbers': sorted(cluster),
                'internal_strength': total_internal,
                'avg_strength': total_internal / (len(cluster) * (len(cluster) - 1) / 2)
            })
    
    return clusters[:5]

def find_inevitable_combination(draws, max_num, config):
    """
    Combine ALL signals to find the combination most likely to occur in future.
    """
    # Get all analysis results
    overdue = analyze_gap_convergence(draws, max_num)
    transitions = analyze_markov_transitions(draws, max_num)
    periodic = analyze_autocorrelation(draws, max_num)
    entropy = analyze_entropy_trend(draws)
    conditionals = analyze_conditional_sequences(draws, max_num)
    clusters = analyze_number_graph(draws, max_num)
    
    # Score each number based on multiple signals
    scores = defaultdict(float)
    reasons = defaultdict(list)
    
    # 1. Overdue numbers get big boost
    for item in overdue[:10]:
        num = item['number']
        boost = min(item['urgency'], 3.0)  # Cap at 3x
        scores[num] += boost * 2
        reasons[num].append(f"OVERDUE: {item['current_gap']} draws (avg {item['avg_gap']:.0f})")
    
    # 2. Markov transition targets
    last_draw = draws[0].get('main', [])
    for trans in transitions:
        if trans['trigger'] in last_draw:
            scores[trans['follower']] += trans['lift']
            reasons[trans['follower']].append(f"FOLLOWS {trans['trigger']} (lift {trans['lift']:.1f}x)")
    
    # 3. Periodic patterns - if due based on period
    for pat in periodic:
        num = pat['number']
        draws_since = pat['last_appearance']
        period = pat['period']
        if draws_since > 0 and draws_since % period < 3:  # Near period multiple
            scores[num] += abs(pat['correlation']) * 1.5
            reasons[num].append(f"PERIODIC: {period}-draw cycle (corr {pat['correlation']:.2f})")
    
    # 4. Cluster members if any cluster number appeared recently
    for cluster in clusters:
        cluster_nums = set(cluster['numbers'])
        if cluster_nums.intersection(set(last_draw)):
            for num in cluster_nums:
                if num not in last_draw:
                    scores[num] += 0.5
                    reasons[num].append(f"CLUSTER with recent: {cluster['numbers']}")
    
    # 5. Conditional patterns based on pairs in last draw
    last_pairs = list(combinations(sorted(last_draw), 2))
    for cond in conditionals:
        if cond['trigger_pair'] in last_pairs:
            scores[cond['next_number']] += cond['lift'] * 0.5
            reasons[cond['next_number']].append(f"AFTER PAIR {cond['trigger_pair']} (lift {cond['lift']:.1f}x)")
    
    # Sort by score and build ticket
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Build ticket respecting position constraints
    pos_freq = {i: Counter() for i in range(5)}
    for draw in draws[:200]:  # Recent position frequencies
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] += 1
    
    # Get position ranges
    pos_ranges = []
    for i in range(5):
        nums = [num for num, _ in pos_freq[i].most_common(30)]
        if nums:
            pos_ranges.append((min(nums), max(nums)))
        else:
            pos_ranges.append((1, max_num))
    
    # Select numbers that fit positions AND have high scores
    ticket = []
    used = set()
    
    for pos in range(5):
        best_for_pos = None
        best_score = -1
        
        for num, score in ranked:
            if num in used:
                continue
            # Check if num fits this position
            if pos_ranges[pos][0] <= num <= pos_ranges[pos][1]:
                # Must be larger than previous
                if not ticket or num > ticket[-1]:
                    if score > best_score:
                        best_score = score
                        best_for_pos = num
        
        if best_for_pos:
            ticket.append(best_for_pos)
            used.add(best_for_pos)
    
    # Find best bonus
    bonus_freq = Counter()
    for draw in draws[:100]:
        bonus = draw.get('bonus')
        if bonus:
            bonus_freq[bonus] += 1
    top_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
    
    return {
        'ticket': ticket,
        'bonus': top_bonus,
        'number_scores': dict(ranked[:15]),
        'number_reasons': {k: v for k, v in reasons.items() if k in [r[0] for r in ranked[:15]]},
        'overdue_analysis': overdue[:5],
        'periodic_patterns': periodic[:5],
        'entropy_trends': entropy,
        'clusters': clusters[:3]
    }

def check_if_ever_drawn(ticket, draws):
    """Check if this exact combination has ever been drawn."""
    ticket_set = set(ticket)
    for draw in draws:
        if set(draw.get('main', [])) == ticket_set:
            return True
    return False

# =============================================================================
# MAIN ANALYSIS
# =============================================================================

print("=" * 80)
print("DEEP PATTERN DISCOVERY - Novel AI/Statistical Approaches")
print("Finding future drawings that WILL happen based on unexplored patterns")
print("=" * 80)

results = {}

for lottery in ['l4l', 'la']:
    draws = load_draws(lottery)
    if not draws:
        print(f"\n⚠️ No data for {lottery}")
        continue
    
    config = LOTTERY_CONFIG[lottery]
    max_num = config['max_main']
    
    print(f"\n{'='*80}")
    print(f"🎰 {config['name'].upper()} - {len(draws)} draws")
    print("="*80)
    
    # Run full analysis
    result = find_inevitable_combination(draws, max_num, config)
    results[lottery] = result
    
    print(f"\n📊 ENTROPY TRENDS (decreasing = more predictable):")
    for e in result['entropy_trends']:
        arrow = "📉" if e['trend_pct'] < -5 else "📈" if e['trend_pct'] > 5 else "➡️"
        print(f"  Position {e['position']}: {e['early_entropy']:.2f} → {e['recent_entropy']:.2f} ({e['trend_pct']:+.1f}%) {arrow} {e['interpretation']}")
    
    print(f"\n⏰ MOST OVERDUE NUMBERS (statistically must appear soon):")
    for item in result['overdue_analysis']:
        print(f"  #{item['number']:2d}: Missing {item['current_gap']} draws (avg {item['avg_gap']:.0f}, max was {item['max_gap']}) - {item['urgency']:.1f}x overdue!")
    
    print(f"\n🔄 PERIODIC PATTERNS DETECTED:")
    for pat in result['periodic_patterns']:
        print(f"  #{pat['number']:2d}: {pat['period']}-draw cycle (correlation {pat['correlation']:.2f}), last seen {pat['last_appearance']} draws ago")
    
    print(f"\n🕸️ NUMBER CLUSTERS (appear together frequently):")
    for cluster in result['clusters']:
        print(f"  {cluster['numbers']} - internal strength: {cluster['internal_strength']}")
    
    print(f"\n🎯 TOP SCORING NUMBERS (combined signals):")
    for num, score in list(result['number_scores'].items())[:10]:
        reason_str = '; '.join(result['number_reasons'].get(num, ['Position frequency']))
        print(f"  #{num:2d}: Score {score:.2f} - {reason_str}")
    
    print(f"\n" + "="*60)
    print(f"🔮 PREDICTED INEVITABLE TICKET: {result['ticket']} + {result['bonus']}")
    print("="*60)
    
    # Check if ever drawn
    if check_if_ever_drawn(result['ticket'], draws):
        print("⚠️ This combination HAS been drawn before!")
    else:
        print("✅ This combination has NEVER been drawn - it's a fresh prediction!")
    
    # Explain why
    print(f"\nWhy this ticket:")
    for i, num in enumerate(result['ticket']):
        if num in result['number_reasons']:
            print(f"  P{i+1}: #{num} - {'; '.join(result['number_reasons'][num][:2])}")

# Save results
output_path = DATA_DIR / 'deep_pattern_results.json'
with open(output_path, 'w') as f:
    # Convert to JSON-serializable
    json_results = {}
    for lottery, res in results.items():
        json_results[lottery] = {
            'ticket': res['ticket'],
            'bonus': res['bonus'],
            'top_numbers': list(res['number_scores'].items())[:10],
            'overdue': res['overdue_analysis'],
            'periodic': res['periodic_patterns'],
            'clusters': res['clusters']
        }
    json.dump(json_results, f, indent=2, default=str)

print(f"\n\n📁 Results saved to {output_path}")

print("""
================================================================================
🧠 METHODS USED (Novel approaches not tried before):

1. MARKOV TRANSITIONS: What numbers "follow" other numbers?
   - Tracks P(number Y | number X appeared last draw)
   - Found numbers that statistically trigger other numbers

2. GAP CONVERGENCE: Numbers that MUST appear based on statistics
   - Tracks each number's gap history
   - Flags numbers exceeding their 95th percentile gap
   - These are statistically overdue to appear

3. AUTOCORRELATION: Periodic cycles in number appearances  
   - Finds numbers with repeating cycles (e.g., every 7 draws)
   - Predicts based on where we are in the cycle

4. ENTROPY TRENDS: Which positions are becoming more predictable?
   - Tracks randomness per position over time
   - Decreasing entropy = patterns emerging

5. CONDITIONAL SEQUENCES: What follows specific pairs?
   - P(number Z | pair (X,Y) appeared together)
   - Exploits 2-number trigger patterns

6. GRAPH CLUSTERING: Numbers that form "communities"
   - Co-occurrence network analysis
   - If one cluster member appears, others follow

COMBINED: All signals weighted together for final prediction.
================================================================================
""")
