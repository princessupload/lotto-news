"""
CRITICAL TICKET AUDIT - Deep verification that HOLD tickets are truly optimal.

Questions to answer:
1. Is pure position frequency actually the best method?
2. How do current tickets compare via backtesting (historical hit rates)?
3. Should we use position freq + pair freq + momentum combined?
4. What about the Jan 12 tickets that had documented 2.98x improvement?
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations

DATA_DIR = Path(__file__).parent / 'data'

# Current tickets - Combined Method Optimal (Jan 23, 2026)
CURRENT_TICKETS = {
    'l4l': {'main': [1, 12, 30, 39, 46], 'bonus': 11},
    'la': {'main': [1, 15, 23, 42, 51], 'bonus': 1},
    'pb': {'main': [1, 11, 27, 53, 68], 'bonus': 20},
    'mm': {'main': [2, 18, 27, 42, 59], 'bonus': 1}
}

# Jan 12 tickets (documented 2.98x improvement, backtested)
JAN12_TICKETS = {
    'l4l': {'main': [1, 12, 30, 39, 47], 'bonus': 11},
    'la': {'main': [2, 15, 27, 42, 51], 'bonus': 4},
    'pb': {'main': [5, 11, 33, 52, 64], 'bonus': 20},
    'mm': {'main': [7, 10, 27, 42, 68], 'bonus': 24}
}

# Ball bias tickets (Jan 22 - problematic)
BALL_BIAS_TICKETS = {
    'l4l': {'main': [3, 12, 17, 38, 46], 'bonus': 11},
    'la': {'main': [4, 15, 25, 42, 51], 'bonus': 4},
    'pb': {'main': [28, 33, 53, 64, 69], 'bonus': 20},
    'mm': {'main': [10, 18, 27, 42, 68], 'bonus': 1}
}

LOTTERY_CONFIG = {
    'l4l': {'name': 'Lucky for Life', 'max_main': 48, 'max_bonus': 18, 'main_count': 5, 'file': 'l4l.json'},
    'la': {'name': 'Lotto America', 'max_main': 52, 'max_bonus': 10, 'main_count': 5, 'file': 'la.json'},
    'pb': {'name': 'Powerball', 'max_main': 69, 'max_bonus': 26, 'main_count': 5, 'file': 'pb.json'},
    'mm': {'name': 'Mega Millions', 'max_main': 70, 'max_bonus': 25, 'main_count': 5, 'file': 'mm.json'}
}

def load_draws(lottery):
    """Load historical draws."""
    config = LOTTERY_CONFIG[lottery]
    file_path = DATA_DIR / config['file']
    if not file_path.exists():
        return []
    with open(file_path) as f:
        data = json.load(f)
    return data.get('draws', [])

def backtest_ticket(ticket_main, ticket_bonus, draws):
    """
    Backtest a ticket against historical draws.
    Returns match counts and statistics.
    """
    results = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    bonus_hits = 0
    matches_detail = []
    
    ticket_set = set(ticket_main)
    
    for draw in draws:
        draw_main = set(draw.get('main', []))
        draw_bonus = draw.get('bonus')
        
        matches = len(ticket_set & draw_main)
        results[matches] += 1
        
        if draw_bonus == ticket_bonus:
            bonus_hits += 1
        
        if matches >= 2:
            matches_detail.append({
                'date': draw.get('date', 'unknown'),
                'matches': matches,
                'bonus_hit': draw_bonus == ticket_bonus,
                'matched_nums': list(ticket_set & draw_main)
            })
    
    total = len(draws)
    return {
        'total_draws': total,
        'results': results,
        'bonus_hits': bonus_hits,
        'bonus_rate': bonus_hits / total if total > 0 else 0,
        '2plus_rate': sum(results[i] for i in range(2, 6)) / total if total > 0 else 0,
        '3plus_rate': sum(results[i] for i in range(3, 6)) / total if total > 0 else 0,
        'best_matches': matches_detail[:10]  # Top 10 best matches
    }

def calculate_position_score(ticket_main, draws):
    """Calculate how well ticket aligns with position frequency."""
    if not draws:
        return 0
    
    score = 0
    for pos in range(5):
        pos_counter = Counter()
        for draw in draws:
            sorted_main = sorted(draw.get('main', []))
            if len(sorted_main) > pos:
                pos_counter[sorted_main[pos]] += 1
        
        # Get ranking of our number in this position
        rankings = pos_counter.most_common()
        our_num = sorted(ticket_main)[pos]
        
        for rank, (num, count) in enumerate(rankings):
            if num == our_num:
                score += (len(rankings) - rank)  # Higher score for higher rank
                break
    
    return score

def calculate_pair_score(ticket_main, draws):
    """Calculate how well ticket uses frequent pairs."""
    pair_counter = Counter()
    for draw in draws:
        main = draw.get('main', [])
        for pair in combinations(sorted(main), 2):
            pair_counter[pair] += 1
    
    score = 0
    ticket_pairs = list(combinations(sorted(ticket_main), 2))
    for pair in ticket_pairs:
        score += pair_counter.get(pair, 0)
    
    return score

def calculate_bonus_score(ticket_bonus, draws):
    """Calculate bonus ball frequency score."""
    bonus_counter = Counter()
    for draw in draws:
        bonus = draw.get('bonus')
        if bonus:
            bonus_counter[bonus] += 1
    
    rankings = bonus_counter.most_common()
    for rank, (num, count) in enumerate(rankings):
        if num == ticket_bonus:
            return len(rankings) - rank
    return 0

def get_truly_optimal_ticket(draws, max_main, max_bonus):
    """
    Calculate the truly optimal ticket using multiple methods combined:
    1. Position frequency (weight: 3)
    2. Pair frequency (weight: 2)
    3. Recent momentum (weight: 1)
    """
    if not draws:
        return None, None
    
    # Position frequency analysis
    pos_freq = [Counter() for _ in range(5)]
    for draw in draws:
        sorted_main = sorted(draw.get('main', []))
        for pos, num in enumerate(sorted_main):
            pos_freq[pos][num] += 1
    
    # Pair frequency
    pair_counter = Counter()
    for draw in draws:
        for pair in combinations(sorted(draw.get('main', [])), 2):
            pair_counter[pair] += 1
    
    # Recent momentum (last 30 draws)
    recent_counter = Counter()
    for draw in draws[:30]:
        for num in draw.get('main', []):
            recent_counter[num] += 1
    
    # Bonus frequency
    bonus_counter = Counter()
    for draw in draws:
        bonus = draw.get('bonus')
        if bonus:
            bonus_counter[bonus] += 1
    
    # Score each number for each position
    ticket = []
    used = set()
    
    for pos in range(5):
        best_num = None
        best_score = -1
        
        # Get valid range for this position
        if pos == 0:
            valid_range = range(1, max_main - 3)
        elif pos == 4:
            valid_range = range(5, max_main + 1)
        else:
            valid_range = range(1, max_main + 1)
        
        for num in valid_range:
            if num in used:
                continue
            
            # Position frequency score (weight 3)
            pos_score = pos_freq[pos].get(num, 0) * 3
            
            # Pair score with already selected numbers (weight 2)
            pair_score = 0
            for prev_num in ticket:
                pair = tuple(sorted([prev_num, num]))
                pair_score += pair_counter.get(pair, 0) * 2
            
            # Momentum score (weight 1)
            momentum_score = recent_counter.get(num, 0)
            
            total_score = pos_score + pair_score + momentum_score
            
            if total_score > best_score:
                best_score = total_score
                best_num = num
        
        if best_num:
            ticket.append(best_num)
            used.add(best_num)
    
    # Best bonus
    best_bonus = bonus_counter.most_common(1)[0][0] if bonus_counter else 1
    
    return sorted(ticket), best_bonus

def main():
    print("=" * 80)
    print("CRITICAL TICKET AUDIT - Are These TRULY the Best Tickets?")
    print("=" * 80)
    
    all_results = {}
    
    for lottery, config in LOTTERY_CONFIG.items():
        draws = load_draws(lottery)
        if not draws:
            print(f"\n⚠️ No data for {config['name']}")
            continue
        
        print(f"\n{'=' * 80}")
        print(f"🎰 {config['name'].upper()} ({len(draws)} draws)")
        print("=" * 80)
        
        # Get tickets to compare
        current = CURRENT_TICKETS[lottery]
        jan12 = JAN12_TICKETS[lottery]
        ball_bias = BALL_BIAS_TICKETS[lottery]
        
        # Calculate truly optimal
        optimal_main, optimal_bonus = get_truly_optimal_ticket(draws, config['max_main'], config['max_bonus'])
        
        tickets_to_test = {
            'Current (Pure Pos Freq)': current,
            'Jan 12 (Backtested)': jan12,
            'Ball Bias (Jan 22)': ball_bias,
            'Combined Method Optimal': {'main': optimal_main, 'bonus': optimal_bonus}
        }
        
        print("\n📊 BACKTEST COMPARISON:")
        print("-" * 70)
        print(f"{'Ticket':<25} {'2+/5 Rate':<12} {'3+/5 Rate':<12} {'Bonus%':<10} {'Score':<10}")
        print("-" * 70)
        
        best_ticket = None
        best_2plus = 0
        
        for name, ticket in tickets_to_test.items():
            bt = backtest_ticket(ticket['main'], ticket['bonus'], draws)
            pos_score = calculate_position_score(ticket['main'], draws)
            pair_score = calculate_pair_score(ticket['main'], draws)
            bonus_score = calculate_bonus_score(ticket['bonus'], draws)
            total_score = pos_score + pair_score + bonus_score
            
            rate_2plus = bt['2plus_rate'] * 100
            rate_3plus = bt['3plus_rate'] * 100
            bonus_rate = bt['bonus_rate'] * 100
            
            marker = ""
            if rate_2plus > best_2plus:
                best_2plus = rate_2plus
                best_ticket = name
            
            print(f"{name:<25} {rate_2plus:>6.2f}%     {rate_3plus:>6.2f}%     {bonus_rate:>5.1f}%    {total_score:>6}")
        
        print("-" * 70)
        print(f"🏆 BEST BY 2+/5 RATE: {best_ticket}")
        
        # Show the tickets
        print(f"\n📋 TICKET DETAILS:")
        for name, ticket in tickets_to_test.items():
            print(f"   {name}: {ticket['main']} + {ticket['bonus']}")
        
        # Check if current is actually optimal
        print(f"\n🔍 ANALYSIS:")
        
        current_bt = backtest_ticket(current['main'], current['bonus'], draws)
        jan12_bt = backtest_ticket(jan12['main'], jan12['bonus'], draws)
        optimal_bt = backtest_ticket(optimal_main, optimal_bonus, draws)
        
        if current['main'] == optimal_main:
            print(f"   ✅ Current ticket matches combined-method optimal")
        else:
            print(f"   ⚠️ Current: {current['main']} + {current['bonus']}")
            print(f"   ⚠️ Optimal: {optimal_main} + {optimal_bonus}")
            
            if optimal_bt['2plus_rate'] > current_bt['2plus_rate']:
                print(f"   📈 Optimal is BETTER: {optimal_bt['2plus_rate']*100:.2f}% vs {current_bt['2plus_rate']*100:.2f}%")
            else:
                print(f"   📊 Current performs same or better in backtest")
        
        # Compare with Jan 12
        if jan12_bt['2plus_rate'] > current_bt['2plus_rate']:
            print(f"\n   ⚠️ JAN 12 TICKET PERFORMS BETTER!")
            print(f"      Jan 12: {jan12_bt['2plus_rate']*100:.2f}% 2+/5 rate")
            print(f"      Current: {current_bt['2plus_rate']*100:.2f}% 2+/5 rate")
            print(f"      Difference: {(jan12_bt['2plus_rate'] - current_bt['2plus_rate'])*100:.2f}%")
        
        all_results[lottery] = {
            'current': current,
            'jan12': jan12,
            'optimal': {'main': optimal_main, 'bonus': optimal_bonus},
            'current_bt': current_bt,
            'jan12_bt': jan12_bt,
            'optimal_bt': optimal_bt
        }
    
    # Final recommendation
    print("\n" + "=" * 80)
    print("📋 FINAL RECOMMENDATIONS")
    print("=" * 80)
    
    needs_change = False
    for lottery, results in all_results.items():
        config = LOTTERY_CONFIG[lottery]
        current = results['current']
        optimal = results['optimal']
        jan12 = results['jan12']
        
        current_rate = results['current_bt']['2plus_rate']
        optimal_rate = results['optimal_bt']['2plus_rate']
        jan12_rate = results['jan12_bt']['2plus_rate']
        
        best_rate = max(current_rate, optimal_rate, jan12_rate)
        
        if current_rate == best_rate:
            print(f"\n✅ {config['name']}: Current ticket is optimal")
            print(f"   {current['main']} + {current['bonus']} ({current_rate*100:.2f}% 2+/5)")
        else:
            needs_change = True
            if jan12_rate == best_rate:
                print(f"\n⚠️ {config['name']}: JAN 12 TICKET IS BETTER!")
                print(f"   Current: {current['main']} + {current['bonus']} ({current_rate*100:.2f}%)")
                print(f"   Better:  {jan12['main']} + {jan12['bonus']} ({jan12_rate*100:.2f}%)")
            else:
                print(f"\n⚠️ {config['name']}: COMBINED METHOD IS BETTER!")
                print(f"   Current: {current['main']} + {current['bonus']} ({current_rate*100:.2f}%)")
                print(f"   Better:  {optimal['main']} + {optimal['bonus']} ({optimal_rate*100:.2f}%)")
    
    if not needs_change:
        print("\n" + "=" * 80)
        print("✅ ALL CURRENT TICKETS ARE OPTIMAL OR TIED FOR BEST")
        print("=" * 80)
    
    # Save results
    with open(DATA_DIR / 'critical_audit_results.json', 'w') as f:
        # Convert to serializable format
        save_results = {}
        for lottery, results in all_results.items():
            save_results[lottery] = {
                'current': results['current'],
                'jan12': results['jan12'],
                'optimal': results['optimal'],
                'current_2plus_rate': results['current_bt']['2plus_rate'],
                'jan12_2plus_rate': results['jan12_bt']['2plus_rate'],
                'optimal_2plus_rate': results['optimal_bt']['2plus_rate']
            }
        json.dump(save_results, f, indent=2)
    
    print(f"\n📁 Results saved to {DATA_DIR / 'critical_audit_results.json'}")

if __name__ == '__main__':
    main()
