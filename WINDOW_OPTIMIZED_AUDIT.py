"""
WINDOW-OPTIMIZED TICKET AUDIT
Uses the correct windows for each lottery as established by walk-forward testing:
- L4L HOLD: 200 draws (or all-time for stability)
- LA HOLD: 200 draws
- PB HOLD: 100 draws (patterns shift faster)
- MM HOLD: All available (only 83 draws)

Also considers separate windows for bonus balls.
"""

import json
from pathlib import Path
from collections import Counter
from itertools import combinations

DATA_DIR = Path(__file__).parent / 'data'

# Optimal windows from walk-forward testing (Jan 21, 2026)
HOLD_WINDOWS = {
    'l4l': {'main': 200, 'bonus': 200, 'name': 'Lucky for Life'},
    'la': {'main': 200, 'bonus': 100, 'name': 'Lotto America'},
    'pb': {'main': 100, 'bonus': 100, 'name': 'Powerball'},
    'mm': {'main': None, 'bonus': None, 'name': 'Mega Millions'}  # Use all (limited data)
}

LOTTERY_CONFIG = {
    'l4l': {'max_main': 48, 'max_bonus': 18},
    'la': {'max_main': 52, 'max_bonus': 10},
    'pb': {'max_main': 69, 'max_bonus': 26},
    'mm': {'max_main': 70, 'max_bonus': 25}
}

def load_draws(lottery):
    """Load historical draws."""
    file_path = DATA_DIR / f'{lottery}.json'
    if not file_path.exists():
        return []
    with open(file_path) as f:
        data = json.load(f)
    return data.get('draws', [])

def get_optimal_main_numbers(draws, window, max_main):
    """
    Get optimal main numbers using:
    1. Position frequency (within window) - weight 3
    2. Pair frequency (within window) - weight 2
    3. Recent momentum (last 30) - weight 1
    """
    if not draws:
        return None
    
    # Apply window
    windowed_draws = draws[:window] if window else draws
    
    # Position frequency analysis
    pos_freq = [Counter() for _ in range(5)]
    for draw in windowed_draws:
        sorted_main = sorted(draw.get('main', []))
        for pos, num in enumerate(sorted_main):
            pos_freq[pos][num] += 1
    
    # Pair frequency
    pair_counter = Counter()
    for draw in windowed_draws:
        for pair in combinations(sorted(draw.get('main', [])), 2):
            pair_counter[pair] += 1
    
    # Recent momentum (last 30 draws of the window)
    momentum_window = min(30, len(windowed_draws))
    recent_counter = Counter()
    for draw in windowed_draws[:momentum_window]:
        for num in draw.get('main', []):
            recent_counter[num] += 1
    
    # Score each number for each position
    ticket = []
    used = set()
    
    for pos in range(5):
        best_num = None
        best_score = -1
        
        # Get candidates from position frequency top performers
        top_candidates = [num for num, _ in pos_freq[pos].most_common(15)]
        
        for num in top_candidates:
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
    
    return sorted(ticket)

def get_optimal_bonus(draws, window, max_bonus):
    """Get optimal bonus using windowed frequency."""
    if not draws:
        return None
    
    # Apply window
    windowed_draws = draws[:window] if window else draws
    
    bonus_counter = Counter()
    for draw in windowed_draws:
        bonus = draw.get('bonus')
        if bonus:
            bonus_counter[bonus] += 1
    
    if not bonus_counter:
        return 1
    
    return bonus_counter.most_common(1)[0][0]

def backtest_ticket(ticket_main, ticket_bonus, draws):
    """Backtest a ticket against ALL historical draws."""
    results = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    bonus_hits = 0
    
    ticket_set = set(ticket_main)
    
    for draw in draws:
        draw_main = set(draw.get('main', []))
        draw_bonus = draw.get('bonus')
        
        matches = len(ticket_set & draw_main)
        results[matches] += 1
        
        if draw_bonus == ticket_bonus:
            bonus_hits += 1
    
    total = len(draws)
    return {
        'total_draws': total,
        'results': results,
        'bonus_hits': bonus_hits,
        'bonus_rate': bonus_hits / total if total > 0 else 0,
        '2plus_rate': sum(results[i] for i in range(2, 6)) / total if total > 0 else 0,
        '3plus_rate': sum(results[i] for i in range(3, 6)) / total if total > 0 else 0,
    }

def main():
    print("=" * 80)
    print("WINDOW-OPTIMIZED TICKET AUDIT")
    print("Using correct windows per lottery for HOLD tickets")
    print("=" * 80)
    
    final_tickets = {}
    
    for lottery, windows in HOLD_WINDOWS.items():
        config = LOTTERY_CONFIG[lottery]
        draws = load_draws(lottery)
        
        if not draws:
            print(f"\n⚠️ No data for {windows['name']}")
            continue
        
        main_window = windows['main']
        bonus_window = windows['bonus']
        
        print(f"\n{'=' * 80}")
        print(f"🎰 {windows['name'].upper()} ({len(draws)} draws)")
        print(f"   Main Window: {main_window or 'ALL'} draws")
        print(f"   Bonus Window: {bonus_window or 'ALL'} draws")
        print("=" * 80)
        
        # Get window-optimized ticket
        optimal_main = get_optimal_main_numbers(draws, main_window, config['max_main'])
        optimal_bonus = get_optimal_bonus(draws, bonus_window, config['max_bonus'])
        
        # Also test with ALL draws for comparison
        alltime_main = get_optimal_main_numbers(draws, None, config['max_main'])
        alltime_bonus = get_optimal_bonus(draws, None, config['max_bonus'])
        
        # Also test with small window (50 draws) for comparison
        small_main = get_optimal_main_numbers(draws, 50, config['max_main'])
        small_bonus = get_optimal_bonus(draws, 50, config['max_bonus'])
        
        tickets_to_test = {
            f'Window {main_window or "ALL"}': {'main': optimal_main, 'bonus': optimal_bonus},
            'All-Time': {'main': alltime_main, 'bonus': alltime_bonus},
            'Recent 50': {'main': small_main, 'bonus': small_bonus},
        }
        
        print("\n📊 WINDOW COMPARISON:")
        print("-" * 70)
        print(f"{'Window':<20} {'Ticket':<30} {'2+/5 Rate':<12} {'Bonus%':<10}")
        print("-" * 70)
        
        best_ticket = None
        best_rate = 0
        best_name = ""
        
        for name, ticket in tickets_to_test.items():
            if not ticket['main']:
                continue
            bt = backtest_ticket(ticket['main'], ticket['bonus'], draws)
            rate_2plus = bt['2plus_rate'] * 100
            bonus_rate = bt['bonus_rate'] * 100
            
            ticket_str = f"{ticket['main']} + {ticket['bonus']}"
            print(f"{name:<20} {ticket_str:<30} {rate_2plus:>6.2f}%     {bonus_rate:>5.1f}%")
            
            if rate_2plus > best_rate:
                best_rate = rate_2plus
                best_ticket = ticket
                best_name = name
        
        print("-" * 70)
        print(f"🏆 BEST: {best_name} with {best_rate:.2f}% 2+/5 rate")
        
        final_tickets[lottery] = {
            'main': best_ticket['main'],
            'bonus': best_ticket['bonus'],
            'window': best_name,
            'rate': best_rate
        }
        
        # Show position frequency breakdown for best ticket
        print(f"\n📋 OPTIMAL TICKET: {best_ticket['main']} + {best_ticket['bonus']}")
        
        # Verify each number is in top positions
        windowed = draws[:main_window] if main_window else draws
        pos_freq = [Counter() for _ in range(5)]
        for draw in windowed:
            sorted_main = sorted(draw.get('main', []))
            for pos, num in enumerate(sorted_main):
                pos_freq[pos][num] += 1
        
        print("\n   Position Analysis:")
        for pos, num in enumerate(sorted(best_ticket['main'])):
            rankings = pos_freq[pos].most_common()
            for rank, (n, count) in enumerate(rankings):
                if n == num:
                    freq = count / len(windowed) * 100
                    print(f"   Pos {pos+1}: #{num} ranked #{rank+1} ({freq:.1f}%)")
                    break
        
        # Bonus analysis
        bonus_counter = Counter()
        bonus_windowed = draws[:bonus_window] if bonus_window else draws
        for draw in bonus_windowed:
            b = draw.get('bonus')
            if b:
                bonus_counter[b] += 1
        
        rankings = bonus_counter.most_common()
        for rank, (n, count) in enumerate(rankings):
            if n == best_ticket['bonus']:
                freq = count / len(bonus_windowed) * 100
                print(f"   Bonus #{best_ticket['bonus']} ranked #{rank+1} ({freq:.1f}%)")
                break
    
    # Final summary
    print("\n" + "=" * 80)
    print("📋 FINAL WINDOW-OPTIMIZED TICKETS")
    print("=" * 80)
    
    for lottery, result in final_tickets.items():
        name = HOLD_WINDOWS[lottery]['name']
        print(f"\n{name}:")
        print(f"   {result['main']} + {result['bonus']}")
        print(f"   Window: {result['window']} | Rate: {result['rate']:.2f}%")
    
    # Save results
    with open(DATA_DIR / 'window_optimized_tickets.json', 'w') as f:
        json.dump(final_tickets, f, indent=2)
    
    print(f"\n📁 Results saved to {DATA_DIR / 'window_optimized_tickets.json'}")

if __name__ == '__main__':
    main()
