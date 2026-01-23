"""
Compare OLD hold tickets vs NEW hold tickets using identical scoring.
Be honest about which is actually better.
"""
import json
from pathlib import Path
from collections import Counter
from itertools import combinations

DATA_DIR = Path(__file__).parent / 'data'

# OLD HOLD tickets (from user_hold_tickets.json and daily_email_report.py)
OLD_TICKETS = {
    'l4l': {'main': [1, 12, 30, 39, 47], 'bonus': 11},  # From daily_email_report.py
    'la':  {'main': [1, 15, 23, 42, 51], 'bonus': 4},
    'pb':  {'main': [1, 11, 33, 52, 69], 'bonus': 20},
    'mm':  {'main': [2, 10, 27, 42, 68], 'bonus': 1}
}

# NEW tickets (from master_jackpot_tickets.json)
NEW_TICKETS = {
    'l4l': {'main': [3, 6, 17, 39, 46], 'bonus': 2},
    'la':  {'main': [8, 11, 30, 47, 51], 'bonus': 4},
    'pb':  {'main': [3, 11, 27, 38, 68], 'bonus': 25},
    'mm':  {'main': [16, 23, 40, 56, 57], 'bonus': 16}
}

def load_draws(lottery):
    path = DATA_DIR / f'{lottery}.json'
    if path.exists():
        with open(path) as f:
            return json.load(f).get('draws', [])
    return []

def calc_position_freqs(draws):
    """Calculate position-specific frequencies."""
    freqs = [{} for _ in range(5)]
    for draw in draws:
        main = sorted(draw['main'])
        for i, num in enumerate(main):
            freqs[i][num] = freqs[i].get(num, 0) + 1
    total = len(draws) or 1
    return [{k: v/total for k, v in f.items()} for f in freqs]

def calc_bonus_freqs(draws):
    freqs = Counter(d['bonus'] for d in draws)
    total = len(draws) or 1
    return {k: v/total for k, v in freqs.items()}

def calc_pair_freqs(draws):
    freqs = Counter()
    for draw in draws:
        for pair in combinations(sorted(draw['main']), 2):
            freqs[pair] += 1
    return freqs

def score_ticket_identical(ticket, bonus, draws, pos_freqs, bonus_freqs, pair_freqs):
    """Score using IDENTICAL methodology for fair comparison."""
    ticket = sorted(ticket)
    score = 0.0
    
    # 1. Position frequency (main factor)
    for i, num in enumerate(ticket):
        score += pos_freqs[i].get(num, 0) * 100
    
    # 2. Pair frequency
    for pair in combinations(ticket, 2):
        score += pair_freqs.get(pair, 0) * 2
    
    # 3. Bonus frequency
    score += bonus_freqs.get(bonus, 0) * 30
    
    # 4. Last draw repeat bonus
    if draws:
        last = set(draws[0]['main'])
        repeats = len(set(ticket) & last)
        score += repeats * 5 * 0.45  # 45% repeat rate
    
    return score

def backtest_ticket(ticket, bonus, draws, window=100):
    """
    Backtest a ticket against historical data.
    Returns how many times it would have matched 2+, 3+, 4+, 5/5.
    """
    ticket = sorted(ticket)
    results = {'2+': 0, '3+': 0, '4+': 0, '5/5': 0, 'jackpot': 0}
    
    for draw in draws[:window]:
        main = sorted(draw['main'])
        matches = len(set(ticket) & set(main))
        bonus_match = (bonus == draw['bonus'])
        
        if matches >= 2:
            results['2+'] += 1
        if matches >= 3:
            results['3+'] += 1
        if matches >= 4:
            results['4+'] += 1
        if matches == 5:
            results['5/5'] += 1
            if bonus_match:
                results['jackpot'] += 1
    
    return results

def main():
    print("="*70)
    print("HONEST COMPARISON: OLD vs NEW HOLD TICKETS")
    print("="*70)
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        draws = load_draws(lottery)
        if not draws:
            continue
        
        pos_freqs = calc_position_freqs(draws)
        bonus_freqs = calc_bonus_freqs(draws)
        pair_freqs = calc_pair_freqs(draws)
        
        old = OLD_TICKETS[lottery]
        new = NEW_TICKETS[lottery]
        
        old_score = score_ticket_identical(old['main'], old['bonus'], draws, pos_freqs, bonus_freqs, pair_freqs)
        new_score = score_ticket_identical(new['main'], new['bonus'], draws, pos_freqs, bonus_freqs, pair_freqs)
        
        # Backtest both
        old_backtest = backtest_ticket(old['main'], old['bonus'], draws, window=len(draws))
        new_backtest = backtest_ticket(new['main'], new['bonus'], draws, window=len(draws))
        
        print(f"\n{lottery.upper()} ({len(draws)} draws)")
        print("-"*50)
        print(f"OLD: {old['main']} + Bonus: {old['bonus']}")
        print(f"     Score: {old_score:.2f}")
        print(f"     Backtest: 2+:{old_backtest['2+']} 3+:{old_backtest['3+']} 4+:{old_backtest['4+']} 5/5:{old_backtest['5/5']}")
        
        print(f"\nNEW: {new['main']} + Bonus: {new['bonus']}")
        print(f"     Score: {new_score:.2f}")
        print(f"     Backtest: 2+:{new_backtest['2+']} 3+:{new_backtest['3+']} 4+:{new_backtest['4+']} 5/5:{new_backtest['5/5']}")
        
        # Which is better?
        if new_score > old_score:
            diff = ((new_score / old_score) - 1) * 100
            print(f"\n✅ NEW is {diff:.1f}% better by score")
        elif old_score > new_score:
            diff = ((old_score / new_score) - 1) * 100
            print(f"\n⚠️ OLD is {diff:.1f}% better by score")
        else:
            print(f"\n➖ Scores are equal")
        
        # Backtest comparison
        if new_backtest['3+'] > old_backtest['3+']:
            print(f"✅ NEW has more 3+ matches historically ({new_backtest['3+']} vs {old_backtest['3+']})")
        elif old_backtest['3+'] > new_backtest['3+']:
            print(f"⚠️ OLD has more 3+ matches historically ({old_backtest['3+']} vs {new_backtest['3+']})")
        else:
            print(f"➖ Same 3+ historical matches")
    
    print("\n" + "="*70)
    print("CRITICAL ASSESSMENT")
    print("="*70)
    print("""
⚠️ IMPORTANT CAVEATS:

1. SCORE ≠ JACKPOT PROBABILITY
   Higher score means numbers appear more often at those positions,
   but past frequency does NOT guarantee future hits.

2. NO 5/5 HAS EVER REPEATED
   Any ticket that hasn't hit before has the same theoretical chance
   as any other valid ticket. Score is about SLIGHT statistical edge.

3. BACKTEST IS DESCRIPTIVE, NOT PREDICTIVE
   Seeing 3/5 matches in history doesn't mean it will hit again.

4. THE HONEST TRUTH:
   - Both OLD and NEW tickets use position frequency
   - The difference in score is typically small
   - Both have the SAME fundamental odds (with a slight edge)
   - Jackpot is still 1 in millions, even with our methods
   
5. RECOMMENDATION:
   If you've been playing the OLD tickets, there's NO strong reason
   to switch unless the NEW tickets score significantly higher (>20%).
   Switching repeatedly hurts because of the 45% repeat bonus -
   sticking with ONE ticket forever is the strategy.
""")

if __name__ == '__main__':
    main()
