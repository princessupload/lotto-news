"""Test different window sizes for PB and MM NEXT PLAY tickets using walk-forward backtesting."""
import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent / 'data'

def load_draws(lottery):
    """Load draws from JSON file."""
    for fn in [f'{lottery}.json', f'{lottery}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                return d.get('draws', d) if isinstance(d, dict) else d
    return []

def generate_ticket_from_window(draws, window_size):
    """Generate a ticket using position frequency from a specific window."""
    if len(draws) < window_size:
        return None, None
    
    recent = draws[:window_size]
    
    # Position frequency
    pos_freq = {i: Counter() for i in range(5)}
    for draw in recent:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] += 1
    
    # Get top number per position (avoiding duplicates)
    ticket = []
    used = set()
    for i in range(5):
        for num, _ in pos_freq[i].most_common(10):
            if num not in used:
                ticket.append(num)
                used.add(num)
                break
    
    if len(ticket) < 5:
        return None, None
    
    # Bonus - most frequent
    bonus_freq = Counter()
    for draw in recent:
        b = draw.get('bonus')
        if b:
            bonus_freq[b] += 1
    top_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
    
    return sorted(ticket), top_bonus

def count_matches(ticket, draw_main):
    """Count how many numbers match."""
    return len(set(ticket) & set(draw_main))

def walk_forward_test(draws, window_size, test_draws=50):
    """
    Walk-forward backtest: For each of the last test_draws,
    generate a ticket using the window BEFORE that draw,
    then check how many numbers matched.
    """
    if len(draws) < window_size + test_draws:
        test_draws = len(draws) - window_size - 1
        if test_draws < 10:
            return None
    
    results = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    bonus_hits = 0
    
    for i in range(test_draws):
        # The draw we're trying to predict
        target_draw = draws[i]
        target_main = target_draw.get('main', [])
        target_bonus = target_draw.get('bonus')
        
        # Generate ticket from window AFTER this draw (older data)
        historical_draws = draws[i+1:]  # Everything before this draw
        ticket, bonus = generate_ticket_from_window(historical_draws, window_size)
        
        if ticket:
            matches = count_matches(ticket, target_main)
            results[matches] += 1
            if bonus == target_bonus:
                bonus_hits += 1
    
    return {
        'window': window_size,
        'tests': test_draws,
        'results': results,
        'bonus_hits': bonus_hits,
        '3+_matches': results[3] + results[4] + results[5],
        '2+_matches': results[2] + results[3] + results[4] + results[5],
        'avg_matches': sum(k * v for k, v in results.items()) / test_draws if test_draws > 0 else 0
    }

print("=" * 70)
print("NEXT PLAY WINDOW TEST - Comparing 22, 30, 35, 40, 45, 50 draws")
print("=" * 70)

windows_to_test = [22, 30, 35, 40, 45, 50]

for lottery in ['pb', 'mm']:
    draws = load_draws(lottery)
    total = len(draws)
    
    print(f"\n{'=' * 70}")
    print(f"{lottery.upper()} - {total} total draws")
    print("=" * 70)
    print(f"{'Window':<10} {'Tests':<8} {'0-match':<10} {'1-match':<10} {'2-match':<10} {'3+-match':<10} {'Avg':<8}")
    print("-" * 70)
    
    best_window = None
    best_3plus = -1
    best_avg = -1
    
    for window in windows_to_test:
        result = walk_forward_test(draws, window, test_draws=100)
        
        if result:
            r = result['results']
            print(f"{window:<10} {result['tests']:<8} {r[0]:<10} {r[1]:<10} {r[2]:<10} {result['3+_matches']:<10} {result['avg_matches']:.2f}")
            
            # Track best by 3+ matches and average
            if result['3+_matches'] > best_3plus or (result['3+_matches'] == best_3plus and result['avg_matches'] > best_avg):
                best_3plus = result['3+_matches']
                best_avg = result['avg_matches']
                best_window = window
        else:
            print(f"{window:<10} Not enough data")
    
    print("-" * 70)
    if best_window:
        print(f"BEST WINDOW FOR {lottery.upper()}: {best_window} draws (3+ matches: {best_3plus}, avg: {best_avg:.2f})")

print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)
print("Choose the window with highest 3+ matches and/or best average.")
print("Smaller windows = more momentum-based (hot streaks)")
print("Larger windows = more stable patterns")
