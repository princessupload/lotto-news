"""
Find patterns that predict FUTURE drawings that have NEVER happened before.
Focus on L4L and LA as they have best odds and most stable patterns.
"""
import json
from pathlib import Path
from collections import Counter
from itertools import combinations

DATA_DIR = Path(__file__).parent / 'data'

def load_draws(lottery):
    for fn in [f'{lottery}.json', f'{lottery}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                return d.get('draws', d) if isinstance(d, dict) else d
    return []

def get_all_combinations_set(draws):
    """Get set of all combinations that have already happened."""
    seen = set()
    for draw in draws:
        main = tuple(sorted(draw.get('main', [])))
        seen.add(main)
    return seen

def analyze_position_trends(draws, window=50):
    """Analyze which numbers are trending UP in each position."""
    if len(draws) < window * 2:
        return None
    
    recent = draws[:window]
    older = draws[window:window*2]
    
    trends = {}
    for pos in range(5):
        recent_freq = Counter()
        older_freq = Counter()
        
        for draw in recent:
            main = sorted(draw.get('main', []))
            if pos < len(main):
                recent_freq[main[pos]] += 1
        
        for draw in older:
            main = sorted(draw.get('main', []))
            if pos < len(main):
                older_freq[main[pos]] += 1
        
        # Find numbers trending UP (more frequent recently)
        trending_up = []
        for num in recent_freq:
            recent_pct = recent_freq[num] / window * 100
            older_pct = older_freq.get(num, 0) / window * 100
            if recent_pct > older_pct + 2:  # At least 2% increase
                trending_up.append((num, recent_pct - older_pct, recent_freq[num]))
        
        trending_up.sort(key=lambda x: x[1], reverse=True)
        trends[pos] = trending_up[:5]  # Top 5 trending
    
    return trends

def find_never_played_combos(draws, max_main, top_per_pos=6):
    """Find statistically likely combinations that have NEVER been drawn."""
    seen = get_all_combinations_set(draws)
    
    # Position frequency from all draws
    pos_freq = {i: Counter() for i in range(5)}
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] += 1
    
    # Get top numbers per position
    top_per = [[n for n, _ in pos_freq[i].most_common(top_per_pos)] for i in range(5)]
    
    # Generate all valid combinations from top numbers
    candidates = []
    for n1 in top_per[0]:
        for n2 in top_per[1]:
            if n2 <= n1: continue
            for n3 in top_per[2]:
                if n3 <= n2: continue
                for n4 in top_per[3]:
                    if n4 <= n3: continue
                    for n5 in top_per[4]:
                        if n5 <= n4: continue
                        combo = (n1, n2, n3, n4, n5)
                        
                        # Skip if already happened
                        if combo in seen:
                            continue
                        
                        # Score by position frequency
                        score = sum(pos_freq[i][combo[i]] for i in range(5))
                        
                        # Constraint filters
                        decades = len(set(n // 10 for n in combo))
                        consecutive = sum(1 for i in range(4) if combo[i+1] - combo[i] == 1)
                        ticket_sum = sum(combo)
                        
                        if decades >= 2 and consecutive <= 1:
                            candidates.append({
                                'combo': combo,
                                'score': score,
                                'sum': ticket_sum,
                                'decades': decades,
                                'consecutive': consecutive
                            })
    
    # Sort by score
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates

def find_due_patterns(draws, window=100):
    """Find patterns that are 'due' based on historical frequency."""
    # Pair frequency
    pair_freq = Counter()
    for draw in draws:
        main = sorted(draw.get('main', []))
        for pair in combinations(main, 2):
            pair_freq[pair] += 1
    
    # Recent pairs (last window)
    recent_pairs = Counter()
    for draw in draws[:window]:
        main = sorted(draw.get('main', []))
        for pair in combinations(main, 2):
            recent_pairs[pair] += 1
    
    # Find pairs that are historically frequent but recently cold
    due_pairs = []
    total = len(draws)
    for pair, count in pair_freq.most_common(100):
        expected_recent = (count / total) * window
        actual_recent = recent_pairs.get(pair, 0)
        if actual_recent < expected_recent * 0.5:  # Less than half expected
            due_pairs.append({
                'pair': pair,
                'historical_freq': count,
                'expected_recent': expected_recent,
                'actual_recent': actual_recent,
                'due_factor': expected_recent / (actual_recent + 0.1)
            })
    
    due_pairs.sort(key=lambda x: x['due_factor'], reverse=True)
    return due_pairs[:10]

def predict_next_combo(draws, max_main):
    """Predict the most likely NEVER-PLAYED combination for the next draw."""
    # Get trending numbers
    trends = analyze_position_trends(draws, window=50)
    
    # Get position frequency
    pos_freq = {i: Counter() for i in range(5)}
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] += 1
    
    # Combine trending + frequency for prediction
    predicted = []
    used = set()
    
    for pos in range(5):
        # Score = frequency + trending bonus
        scores = {}
        for num, _ in pos_freq[pos].most_common(15):
            base_score = pos_freq[pos][num]
            trend_bonus = 0
            if trends and pos in trends:
                for t_num, t_change, _ in trends[pos]:
                    if t_num == num:
                        trend_bonus = t_change * 2  # Boost trending numbers
                        break
            scores[num] = base_score + trend_bonus
        
        # Pick best that maintains ascending order
        sorted_nums = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for num, score in sorted_nums:
            if num not in used:
                if not predicted or num > predicted[-1]:
                    predicted.append(num)
                    used.add(num)
                    break
    
    return predicted if len(predicted) == 5 else None

# ============================================================
# MAIN ANALYSIS
# ============================================================

print("=" * 80)
print("FUTURE PATTERN ANALYSIS - Finding Never-Played Likely Combinations")
print("=" * 80)

for lottery in ['l4l', 'la']:
    draws = load_draws(lottery)
    if not draws:
        continue
    
    name = 'Lucky for Life' if lottery == 'l4l' else 'Lotto America'
    max_main = 48 if lottery == 'l4l' else 52
    seen = get_all_combinations_set(draws)
    
    print(f"\n{'=' * 80}")
    print(f"{name.upper()} - {len(draws)} draws analyzed")
    print(f"Total unique combinations ever drawn: {len(seen)}")
    print("=" * 80)
    
    # 1. Position Trends
    print(f"\n📈 TRENDING UP (Numbers gaining frequency):")
    trends = analyze_position_trends(draws, window=50)
    if trends:
        for pos in range(5):
            if trends[pos]:
                top = trends[pos][0]
                print(f"   Position {pos+1}: {top[0]} (+{top[1]:.1f}% vs previous 50)")
    
    # 2. Due Pairs
    print(f"\n⏰ DUE PAIRS (Historically frequent, recently cold):")
    due_pairs = find_due_patterns(draws, window=100)
    for dp in due_pairs[:5]:
        print(f"   {dp['pair']}: {dp['actual_recent']}/{dp['expected_recent']:.1f} recent (due factor: {dp['due_factor']:.1f}x)")
    
    # 3. Never-Played High-Score Combos
    print(f"\n🎯 TOP 10 NEVER-PLAYED COMBINATIONS (Highest position frequency score):")
    never_played = find_never_played_combos(draws, max_main, top_per_pos=8)
    for i, np in enumerate(never_played[:10], 1):
        print(f"   #{i}: {list(np['combo'])} (score: {np['score']}, sum: {np['sum']})")
    
    # 4. Predicted Next Combo
    print(f"\n🔮 PREDICTED MOST LIKELY NEXT COMBO (Trend + Frequency):")
    predicted = predict_next_combo(draws, max_main)
    if predicted:
        # Check if it's never been played
        if tuple(predicted) not in seen:
            print(f"   {predicted} - NEVER PLAYED BEFORE! ✨")
        else:
            print(f"   {predicted} - (has been played before)")
    
    # 5. Bonus ball prediction
    bonus_freq = Counter()
    for draw in draws[:100]:
        b = draw.get('bonus')
        if b:
            bonus_freq[b] += 1
    top_bonus = bonus_freq.most_common(3)
    print(f"\n🎱 TOP BONUS BALLS (Last 100 draws): {[b for b, _ in top_bonus]}")

print("\n" + "=" * 80)
print("SUMMARY: BEST NEVER-PLAYED TICKETS TO CONSIDER")
print("=" * 80)

for lottery in ['l4l', 'la']:
    draws = load_draws(lottery)
    name = 'Lucky for Life' if lottery == 'l4l' else 'Lotto America'
    max_main = 48 if lottery == 'l4l' else 52
    
    never_played = find_never_played_combos(draws, max_main, top_per_pos=8)
    bonus_freq = Counter()
    for draw in draws[:100]:
        b = draw.get('bonus')
        if b:
            bonus_freq[b] += 1
    top_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
    
    if never_played:
        best = never_played[0]
        print(f"\n{name}:")
        print(f"   🎫 {list(best['combo'])} + Bonus: {top_bonus}")
        print(f"   📊 Never played | Score: {best['score']} | Sum: {best['sum']}")
