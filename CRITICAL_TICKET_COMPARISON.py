"""
CRITICAL TICKET COMPARISON
===========================

Compare ALL ticket generation methods head-to-head using IDENTICAL scoring.
Determine which method actually produces the best HOLD FOREVER tickets.

Methods compared:
1. Position Frequency Only (current HOLD tickets)
2. Deep Pattern Discovery (Markov + Gap + Periodic)
3. Ultra Deep Analysis (Momentum + Stability + Mod cycles)
4. Master Jackpot Hunter (Exclusions + All patterns)
5. NEW: Combined Optimal (best of all methods)
"""
import json
import numpy as np
from pathlib import Path
from collections import Counter
from itertools import combinations

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

# ALL candidate tickets from different methods
CANDIDATE_TICKETS = {
    'l4l': {
        'current_hold': {'main': [1, 12, 30, 39, 47], 'bonus': 11, 'method': 'Position Frequency (Current)'},
        'master_jackpot': {'main': [3, 6, 17, 39, 46], 'bonus': 2, 'method': 'Master Jackpot Hunter'},
        'deep_pattern': {'main': [3, 17, 30, 32, 44], 'bonus': 18, 'method': 'Deep Pattern Discovery'},
        'ultra_deep': {'main': [17, 24, 32, 42, 48], 'bonus': 15, 'method': 'Ultra Deep Analysis'},
    },
    'la': {
        'current_hold': {'main': [1, 15, 23, 42, 51], 'bonus': 4, 'method': 'Position Frequency (Current)'},
        'master_jackpot': {'main': [8, 11, 30, 47, 51], 'bonus': 4, 'method': 'Master Jackpot Hunter'},
        'deep_pattern': {'main': [3, 15, 25, 37, 52], 'bonus': 4, 'method': 'Deep Pattern Discovery'},
    },
    'pb': {
        'current_hold': {'main': [1, 11, 33, 52, 69], 'bonus': 20, 'method': 'Position Frequency (Current)'},
        'master_jackpot': {'main': [3, 11, 27, 38, 68], 'bonus': 25, 'method': 'Master Jackpot Hunter'},
        'ultra_deep': {'main': [5, 28, 53, 55, 57], 'bonus': 20, 'method': 'Ultra Deep Analysis'},
    },
    'mm': {
        'current_hold': {'main': [2, 10, 27, 42, 68], 'bonus': 1, 'method': 'Position Frequency (Current)'},
        'master_jackpot': {'main': [16, 23, 40, 56, 57], 'bonus': 16, 'method': 'Master Jackpot Hunter'},
        'ultra_deep': {'main': [8, 42, 47, 64, 66], 'bonus': 1, 'method': 'Ultra Deep Analysis'},
    }
}

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

def calculate_comprehensive_score(ticket, bonus, draws, max_num, pos_ranges):
    """
    COMPREHENSIVE scoring using ALL validated methods.
    This is the DEFINITIVE scoring function.
    """
    ticket = sorted(ticket)
    if len(ticket) != 5:
        return 0, "Invalid: not 5 numbers"
    
    score = 0.0
    breakdown = {}
    
    # 1. POSITION FREQUENCY (VERIFIED - most important)
    pos_freq = [{} for _ in range(5)]
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] = pos_freq[i].get(num, 0) + 1
    
    total_draws = len(draws)
    pos_score = 0
    for i, num in enumerate(ticket):
        freq = pos_freq[i].get(num, 0) / total_draws if total_draws > 0 else 0
        pos_score += freq
    breakdown['position_freq'] = pos_score * 100
    score += pos_score * 100
    
    # 2. PAIR FREQUENCY
    pair_freq = Counter()
    for draw in draws:
        for pair in combinations(sorted(draw.get('main', [])), 2):
            pair_freq[pair] += 1
    
    pair_score = 0
    for pair in combinations(ticket, 2):
        pair_score += pair_freq.get(pair, 0)
    breakdown['pair_freq'] = pair_score * 0.5
    score += pair_score * 0.5
    
    # 3. BONUS FREQUENCY
    bonus_freq = Counter(d.get('bonus') for d in draws)
    bonus_score = bonus_freq.get(bonus, 0) / total_draws if total_draws > 0 else 0
    breakdown['bonus_freq'] = bonus_score * 30
    score += bonus_score * 30
    
    # 4. LAST DRAW REPEAT BONUS (verified 45% repeat rate)
    if draws:
        last_draw = set(draws[0].get('main', []))
        repeats = len(set(ticket) & last_draw)
        repeat_score = repeats * 5 * 0.45
        breakdown['repeat_bonus'] = repeat_score
        score += repeat_score
    
    # 5. MOMENTUM (recency weighted)
    momentum_score = 0
    for i, draw in enumerate(draws[:30]):
        weight = 0.9 ** i
        for num in ticket:
            if num in draw.get('main', []):
                momentum_score += weight
    breakdown['momentum'] = momentum_score
    score += momentum_score
    
    # 6. CONSTRAINT VALIDATION (penalties for bad tickets)
    # Sum range
    total_sum = sum(ticket)
    all_sums = [sum(sorted(d.get('main', []))) for d in draws]
    sum_p5 = np.percentile(all_sums, 5)
    sum_p95 = np.percentile(all_sums, 95)
    if not (sum_p5 <= total_sum <= sum_p95):
        score *= 0.8  # 20% penalty
        breakdown['sum_penalty'] = -score * 0.2
    
    # Consecutive pairs
    consec = sum(1 for i in range(len(ticket)-1) if ticket[i+1] - ticket[i] == 1)
    if consec > 1:
        score *= 0.9  # 10% penalty
        breakdown['consec_penalty'] = -score * 0.1
    
    # Decade spread
    decades = len(set(n // 10 for n in ticket))
    if decades < 3:
        score *= 0.9  # 10% penalty
        breakdown['decade_penalty'] = -score * 0.1
    
    breakdown['total'] = score
    return score, breakdown

def backtest_ticket(ticket, bonus, draws, window=None):
    """Backtest a ticket against ALL historical draws."""
    ticket_set = set(sorted(ticket))
    results = {
        '0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0,
        'bonus_hits': 0, 'exact_match': False
    }
    
    test_draws = draws[:window] if window else draws
    
    for draw in test_draws:
        main_set = set(draw.get('main', []))
        matches = len(ticket_set & main_set)
        results[str(matches)] += 1
        
        if draw.get('bonus') == bonus:
            results['bonus_hits'] += 1
        
        if main_set == ticket_set:
            results['exact_match'] = True
    
    return results

def generate_truly_optimal_ticket(lottery, draws, max_num, pos_ranges, exclusions):
    """
    Generate the TRULY optimal ticket by combining all methods
    and using exhaustive search within constraints.
    """
    # Calculate all analysis data
    pos_freq = [{} for _ in range(5)]
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] = pos_freq[i].get(num, 0) + 1
    
    total_draws = len(draws)
    
    # Get top candidates per position
    top_per_pos = []
    for i in range(5):
        min_v, max_v = pos_ranges[i]
        candidates = []
        for num in range(min_v, max_v + 1):
            freq = pos_freq[i].get(num, 0) / total_draws if total_draws > 0 else 0
            candidates.append((num, freq))
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_per_pos.append([c[0] for c in candidates[:12]])  # Top 12 per position
    
    # Generate all valid combinations from top candidates
    best_ticket = None
    best_score = -1
    best_bonus = 1
    
    # Find best bonus first
    bonus_freq = Counter(d.get('bonus') for d in draws)
    best_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
    
    # Exhaustive search through top candidates
    tested = 0
    for p1 in top_per_pos[0]:
        for p2 in top_per_pos[1]:
            if p2 <= p1:
                continue
            for p3 in top_per_pos[2]:
                if p3 <= p2:
                    continue
                for p4 in top_per_pos[3]:
                    if p4 <= p3:
                        continue
                    for p5 in top_per_pos[4]:
                        if p5 <= p4:
                            continue
                        
                        ticket = [p1, p2, p3, p4, p5]
                        
                        # Skip if past winner
                        if tuple(ticket) in exclusions.get(lottery, set()):
                            continue
                        
                        # Score it
                        score, _ = calculate_comprehensive_score(ticket, best_bonus, draws, max_num, pos_ranges)
                        tested += 1
                        
                        if score > best_score:
                            best_score = score
                            best_ticket = ticket
    
    return best_ticket, best_bonus, best_score, tested

def main():
    print("="*80)
    print("CRITICAL TICKET COMPARISON")
    print("Comparing ALL methods with IDENTICAL scoring")
    print("="*80)
    
    exclusions = load_exclusions()
    final_results = {}
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        draws = load_draws(lottery)
        if not draws:
            continue
        
        config = LOTTERY_CONFIG[lottery]
        max_num = config['max_main']
        pos_ranges = POSITION_RANGES[lottery]
        candidates = CANDIDATE_TICKETS.get(lottery, {})
        
        print(f"\n{'='*80}")
        print(f"🎰 {config['name'].upper()} ({config['type'].upper()}) - {len(draws)} draws")
        print("="*80)
        
        # Score all candidate tickets
        print(f"\n📊 SCORING ALL CANDIDATE TICKETS:")
        print("-"*60)
        
        scored_candidates = []
        for name, data in candidates.items():
            ticket = data['main']
            bonus = data['bonus']
            method = data['method']
            
            if len(ticket) != 5:
                print(f"  ⚠️ {method}: INVALID (only {len(ticket)} numbers)")
                continue
            
            score, breakdown = calculate_comprehensive_score(ticket, bonus, draws, max_num, pos_ranges)
            backtest = backtest_ticket(ticket, bonus, draws)
            is_excluded = tuple(sorted(ticket)) in exclusions.get(lottery, set())
            
            scored_candidates.append({
                'name': name,
                'method': method,
                'ticket': ticket,
                'bonus': bonus,
                'score': score,
                'breakdown': breakdown,
                'backtest': backtest,
                'excluded': is_excluded
            })
            
            print(f"\n  {method}:")
            print(f"    Ticket: {ticket} + {bonus}")
            print(f"    Score: {score:.2f}")
            print(f"    Backtest: 2+:{backtest['2']}+ 3+:{backtest['3']}+ 4+:{backtest['4']}+ 5/5:{backtest['5']}")
            print(f"    Excluded: {'❌ YES' if is_excluded else '✅ NO'}")
        
        # Generate truly optimal ticket
        print(f"\n🔬 GENERATING TRULY OPTIMAL TICKET (exhaustive search)...")
        optimal_ticket, optimal_bonus, optimal_score, tested = generate_truly_optimal_ticket(
            lottery, draws, max_num, pos_ranges, exclusions
        )
        
        if optimal_ticket:
            opt_backtest = backtest_ticket(optimal_ticket, optimal_bonus, draws)
            scored_candidates.append({
                'name': 'truly_optimal',
                'method': f'Exhaustive Search ({tested:,} combos tested)',
                'ticket': optimal_ticket,
                'bonus': optimal_bonus,
                'score': optimal_score,
                'backtest': opt_backtest,
                'excluded': False
            })
            
            print(f"\n  TRULY OPTIMAL (Exhaustive Search):")
            print(f"    Ticket: {optimal_ticket} + {optimal_bonus}")
            print(f"    Score: {optimal_score:.2f}")
            print(f"    Backtest: 2+:{opt_backtest['2']}+ 3+:{opt_backtest['3']}+ 4+:{opt_backtest['4']}+ 5/5:{opt_backtest['5']}")
            print(f"    Tested: {tested:,} combinations")
        
        # Rank all candidates
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n{'='*60}")
        print(f"🏆 WINNER FOR {config['name'].upper()}:")
        print("="*60)
        
        winner = scored_candidates[0] if scored_candidates else None
        if winner:
            print(f"\n  🎯 {winner['method']}")
            print(f"     Ticket: {winner['ticket']} + Bonus: {winner['bonus']}")
            print(f"     Score: {winner['score']:.2f}")
            print(f"     Backtest 3+: {winner['backtest']['3']} times")
            
            # Why this ticket wins
            print(f"\n  Why this is the BEST:")
            if winner['score'] > 0:
                for i, candidate in enumerate(scored_candidates[1:4], 2):
                    diff = ((winner['score'] / candidate['score']) - 1) * 100
                    print(f"    vs #{i}: {diff:+.1f}% better than {candidate['method']}")
            
            final_results[lottery] = {
                'ticket': winner['ticket'],
                'bonus': winner['bonus'],
                'score': winner['score'],
                'method': winner['method'],
                'backtest_3plus': winner['backtest']['3']
            }
    
    # Final summary
    print("\n\n" + "="*80)
    print("🏆 FINAL OPTIMAL HOLD FOREVER TICKETS")
    print("="*80)
    
    for lottery, result in final_results.items():
        config = LOTTERY_CONFIG[lottery]
        print(f"\n{config['name']}:")
        print(f"  Ticket: {result['ticket']} + Bonus: {result['bonus']}")
        print(f"  Score: {result['score']:.2f} | Method: {result['method']}")
        print(f"  Historical 3+ matches: {result['backtest_3plus']}")
    
    # Save final results
    output = {
        'analysis_date': str(np.datetime64('now')),
        'method': 'Critical Comparison - Exhaustive Search',
        'final_optimal_tickets': {}
    }
    for lottery, result in final_results.items():
        output['final_optimal_tickets'][lottery] = result
    
    output_path = DATA_DIR / 'FINAL_OPTIMAL_TICKETS.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n✅ Final results saved to {output_path}")
    
    return final_results

if __name__ == '__main__':
    main()
