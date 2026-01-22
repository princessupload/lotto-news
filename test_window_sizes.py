#!/usr/bin/env python3
"""
Walk-Forward Backtest: Test different window sizes for PB and MM
Tests the theory that smaller windows work better for NEXT PLAY tickets
and 100-draw window works better for HOLD tickets.
"""

import json
from pathlib import Path
from collections import Counter
from datetime import datetime

DATA_DIR = Path(__file__).parent / 'data'

def load_draws(lottery_key):
    """Load draws from JSON file."""
    filepath = DATA_DIR / f'{lottery_key}.json'
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('draws', [])
    return []

def get_position_frequencies(draws, window_size=None):
    """Get position frequency for each position (1-5) from draws."""
    if window_size:
        draws = draws[:window_size]
    
    position_counts = [Counter() for _ in range(5)]
    bonus_counts = Counter()
    
    for draw in draws:
        main = sorted(draw['main'])
        for i, num in enumerate(main):
            position_counts[i][num] += 1
        bonus_counts[draw['bonus']] += 1
    
    return position_counts, bonus_counts

def generate_ticket_from_window(draws, window_size, max_main, max_bonus):
    """Generate optimal ticket from window using position frequency."""
    pos_counts, bonus_counts = get_position_frequencies(draws, window_size)
    
    ticket = []
    used = set()
    
    for i in range(5):
        # Get most frequent number for this position that hasn't been used
        for num, _ in pos_counts[i].most_common():
            if num not in used:
                ticket.append(num)
                used.add(num)
                break
    
    # Fill any gaps (shouldn't happen but safety)
    while len(ticket) < 5:
        for n in range(1, max_main + 1):
            if n not in used:
                ticket.append(n)
                used.add(n)
                break
    
    bonus = bonus_counts.most_common(1)[0][0] if bonus_counts else 1
    
    return sorted(ticket), bonus

def count_matches(ticket, bonus, draw):
    """Count how many numbers match."""
    draw_main = set(draw['main'])
    ticket_set = set(ticket)
    main_matches = len(ticket_set & draw_main)
    bonus_match = 1 if bonus == draw['bonus'] else 0
    return main_matches, bonus_match

def walk_forward_test(lottery_key, window_sizes, train_size=50, test_size=10):
    """
    Walk-forward backtest for different window sizes.
    
    For each test:
    1. Use 'window_size' draws to generate a ticket
    2. Test that ticket on the next 'test_size' draws
    3. Move forward and repeat
    """
    draws = load_draws(lottery_key)
    
    if lottery_key == 'pb':
        max_main, max_bonus = 69, 26
    elif lottery_key == 'mm':
        max_main, max_bonus = 70, 25
    else:
        max_main, max_bonus = 69, 26
    
    print(f"\n{'='*70}")
    print(f"WALK-FORWARD BACKTEST: {lottery_key.upper()}")
    print(f"Total draws available: {len(draws)}")
    print(f"Test size: {test_size} draws per position")
    print(f"{'='*70}")
    
    results = {}
    
    for window in window_sizes:
        total_tests = 0
        total_2plus = 0
        total_3plus = 0
        total_main_matches = 0
        total_bonus_matches = 0
        
        # Walk through the data
        # Start from where we have enough history
        start_pos = max(window, train_size)
        
        for pos in range(start_pos, len(draws) - test_size, test_size):
            # Get training data (window before current position)
            train_draws = draws[pos - window:pos]
            
            # Generate ticket from training window
            ticket, bonus = generate_ticket_from_window(train_draws, window, max_main, max_bonus)
            
            # Test on next test_size draws
            test_draws = draws[pos:pos + test_size]
            
            for test_draw in test_draws:
                main_matches, bonus_match = count_matches(ticket, bonus, test_draw)
                total_tests += 1
                total_main_matches += main_matches
                total_bonus_matches += bonus_match
                
                if main_matches >= 2:
                    total_2plus += 1
                if main_matches >= 3:
                    total_3plus += 1
        
        if total_tests > 0:
            avg_matches = total_main_matches / total_tests
            pct_2plus = (total_2plus / total_tests) * 100
            pct_3plus = (total_3plus / total_tests) * 100
            bonus_pct = (total_bonus_matches / total_tests) * 100
            
            # Random baseline for comparison
            # 2+/5 random odds: ~3.2% for PB, ~3.0% for MM
            random_2plus = 3.2 if lottery_key == 'pb' else 3.0
            improvement = pct_2plus / random_2plus if random_2plus > 0 else 1.0
            
            results[window] = {
                'tests': total_tests,
                'avg_matches': avg_matches,
                'pct_2plus': pct_2plus,
                'pct_3plus': pct_3plus,
                'bonus_pct': bonus_pct,
                'improvement': improvement
            }
            
            print(f"\nWindow: {window:3d} draws")
            print(f"  Tests: {total_tests}")
            print(f"  Avg main matches: {avg_matches:.2f}/5")
            print(f"  2+/5 rate: {pct_2plus:.2f}% ({improvement:.2f}x vs random)")
            print(f"  3+/5 rate: {pct_3plus:.2f}%")
            print(f"  Bonus hit: {bonus_pct:.1f}%")
    
    # Find best window
    if results:
        best_window = max(results.keys(), key=lambda w: results[w]['pct_2plus'])
        print(f"\n{'='*70}")
        print(f"BEST WINDOW FOR {lottery_key.upper()}: {best_window} draws")
        print(f"  2+/5 rate: {results[best_window]['pct_2plus']:.2f}%")
        print(f"  Improvement: {results[best_window]['improvement']:.2f}x vs random")
        print(f"{'='*70}")
        
        return best_window, results
    
    return None, results

def test_hold_vs_recent(lottery_key, recent_window=100):
    """Compare all-time HOLD ticket vs recent-window HOLD ticket."""
    draws = load_draws(lottery_key)
    
    if lottery_key == 'pb':
        max_main, max_bonus = 69, 26
    elif lottery_key == 'mm':
        max_main, max_bonus = 70, 25
    else:
        max_main, max_bonus = 69, 26
    
    print(f"\n{'='*70}")
    print(f"HOLD TICKET COMPARISON: {lottery_key.upper()}")
    print(f"All-time ({len(draws)} draws) vs Recent ({recent_window} draws)")
    print(f"{'='*70}")
    
    # Generate tickets from different windows
    all_time_ticket, all_time_bonus = generate_ticket_from_window(draws, len(draws), max_main, max_bonus)
    recent_ticket, recent_bonus = generate_ticket_from_window(draws, recent_window, max_main, max_bonus)
    
    print(f"\nAll-time ticket: {all_time_ticket} + {all_time_bonus}")
    print(f"Recent-{recent_window} ticket: {recent_ticket} + {recent_bonus}")
    
    # Test both on recent draws (last 50)
    test_draws = draws[:50]
    
    all_time_matches = {'2plus': 0, '3plus': 0, 'bonus': 0}
    recent_matches = {'2plus': 0, '3plus': 0, 'bonus': 0}
    
    for draw in test_draws:
        # All-time ticket
        main_m, bonus_m = count_matches(all_time_ticket, all_time_bonus, draw)
        if main_m >= 2:
            all_time_matches['2plus'] += 1
        if main_m >= 3:
            all_time_matches['3plus'] += 1
        if bonus_m:
            all_time_matches['bonus'] += 1
        
        # Recent ticket
        main_m, bonus_m = count_matches(recent_ticket, recent_bonus, draw)
        if main_m >= 2:
            recent_matches['2plus'] += 1
        if main_m >= 3:
            recent_matches['3plus'] += 1
        if bonus_m:
            recent_matches['bonus'] += 1
    
    print(f"\nResults on last 50 draws:")
    print(f"  All-time:  2+/5: {all_time_matches['2plus']}/50 ({all_time_matches['2plus']*2}%), 3+/5: {all_time_matches['3plus']}, Bonus: {all_time_matches['bonus']}")
    print(f"  Recent-{recent_window}: 2+/5: {recent_matches['2plus']}/50 ({recent_matches['2plus']*2}%), 3+/5: {recent_matches['3plus']}, Bonus: {recent_matches['bonus']}")
    
    if recent_matches['2plus'] > all_time_matches['2plus']:
        print(f"\n✅ RECENT-{recent_window} WINDOW WINS for {lottery_key.upper()}!")
    elif recent_matches['2plus'] < all_time_matches['2plus']:
        print(f"\n✅ ALL-TIME WINDOW WINS for {lottery_key.upper()}!")
    else:
        print(f"\n⚖️ TIE - Both perform equally for {lottery_key.upper()}")
    
    return all_time_matches, recent_matches

def main():
    print("\n" + "="*70)
    print("LOTTERY WINDOW SIZE OPTIMIZATION TEST")
    print("Testing user theory: smaller windows for NEXT PLAY, 100 for HOLD")
    print("="*70)
    
    # Test window sizes for NEXT PLAY
    window_sizes = [10, 20, 30, 50, 100, 150, 200, 300]
    
    print("\n" + "#"*70)
    print("PART 1: NEXT PLAY OPTIMAL WINDOW SIZE")
    print("#"*70)
    
    # Test PB
    pb_best, pb_results = walk_forward_test('pb', window_sizes)
    
    # Test MM
    mm_best, mm_results = walk_forward_test('mm', window_sizes)
    
    print("\n" + "#"*70)
    print("PART 2: HOLD TICKET - ALL-TIME vs 100-DRAW WINDOW")
    print("#"*70)
    
    # Test HOLD strategy
    test_hold_vs_recent('pb', 100)
    test_hold_vs_recent('mm', 100)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\nPB NEXT PLAY optimal window: {pb_best} draws")
    print(f"MM NEXT PLAY optimal window: {mm_best} draws")
    print("\nSee above for HOLD ticket comparison.")
    print("="*70)

if __name__ == '__main__':
    main()
