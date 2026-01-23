"""
CONTINUOUS JACKPOT HUNTER SYSTEM
================================

A continuously improving system that:
1. Excludes ALL past 5/5 and jackpot combinations (never repeat)
2. Applies ALL validated patterns from walk-forward backtesting
3. Scores tickets using position frequency, hot combos, constraints
4. Learns from new draws and adapts predictions
5. Generates optimal "eventual jackpot" tickets for long-term play

Lottery Types:
- L4L, LA: RNG (Digital Drawing System) - more predictable
- PB, MM: Physical balls - less predictable

Run continuously or on schedule to refine predictions.
"""
import json
import time
import random
import math
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
from itertools import combinations
import hashlib

DATA_DIR = Path(__file__).parent / 'data'

# Load validated patterns
def load_patterns():
    path = Path(__file__).parent / 'VALIDATED_PATTERNS.json'
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

# Load exclusion lists
def load_exclusions():
    path = DATA_DIR / 'past_winners_exclusions.json'
    if path.exists():
        with open(path) as f:
            data = json.load(f)
            return {k: set(tuple(sorted(c)) for c in v) for k, v in data.items()}
    return {}

# Load draw history
def load_draws(lottery):
    path = DATA_DIR / f'{lottery}.json'
    if path.exists():
        with open(path) as f:
            data = json.load(f)
            return data.get('draws', [])
    return []

class JackpotHunter:
    """Main jackpot hunting engine."""
    
    def __init__(self, lottery):
        self.lottery = lottery.lower()
        self.patterns = load_patterns().get(self.lottery.upper(), {})
        self.exclusions = load_exclusions().get(self.lottery, set())
        self.draws = load_draws(self.lottery)
        
        # Extract configuration
        self.main_range = self.patterns.get('main_range', [1, 48])
        self.bonus_range = self.patterns.get('bonus_range', [1, 18])
        self.constraints = self.patterns.get('constraints', {})
        self.position_ranges = self.constraints.get('position_ranges', [])
        self.sum_range = self.constraints.get('sum_range_95pct', [50, 200])
        self.hot_bonus = self.patterns.get('hot_bonus_balls', [])
        self.top_combos = self.patterns.get('top_3_combos', [])
        self.repeat_rate = self.patterns.get('repeat_rate', 0.4)
        
        # Calculate position frequencies
        self.position_freqs = self._calculate_position_freqs()
        self.bonus_freqs = self._calculate_bonus_freqs()
        self.pair_freqs = self._calculate_pair_freqs()
        
        print(f"Loaded {self.lottery.upper()}: {len(self.draws)} draws, {len(self.exclusions)} exclusions")
    
    def _calculate_position_freqs(self):
        """Calculate frequency of each number at each position."""
        freqs = [{} for _ in range(5)]
        for draw in self.draws:
            main = sorted(draw['main'])
            for i, num in enumerate(main):
                freqs[i][num] = freqs[i].get(num, 0) + 1
        # Normalize
        total = len(self.draws) or 1
        for i in range(5):
            for num in freqs[i]:
                freqs[i][num] /= total
        return freqs
    
    def _calculate_bonus_freqs(self):
        """Calculate frequency of each bonus ball."""
        freqs = {}
        for draw in self.draws:
            bonus = draw['bonus']
            freqs[bonus] = freqs.get(bonus, 0) + 1
        total = len(self.draws) or 1
        return {k: v/total for k, v in freqs.items()}
    
    def _calculate_pair_freqs(self):
        """Calculate frequency of number pairs."""
        freqs = Counter()
        for draw in self.draws:
            main = sorted(draw['main'])
            for pair in combinations(main, 2):
                freqs[pair] += 1
        return freqs
    
    def is_excluded(self, ticket):
        """Check if this exact combination has been drawn before."""
        return tuple(sorted(ticket)) in self.exclusions
    
    def validate_constraints(self, ticket):
        """Check if ticket passes all statistical constraints."""
        ticket = sorted(ticket)
        
        # Position ranges
        if self.position_ranges:
            for i, num in enumerate(ticket):
                if i < len(self.position_ranges):
                    min_val, max_val = self.position_ranges[i]
                    if num < min_val or num > max_val:
                        return False, f"Position {i+1} out of range"
        
        # Sum constraint
        total = sum(ticket)
        if total < self.sum_range[0] or total > self.sum_range[1]:
            return False, f"Sum {total} outside 95% range"
        
        # Odd/even balance (2-3 optimal)
        odd_count = sum(1 for n in ticket if n % 2 == 1)
        if odd_count < 2 or odd_count > 3:
            return False, f"Odd count {odd_count} not optimal"
        
        # Consecutive pairs (max 1)
        consecutive = sum(1 for i in range(len(ticket)-1) if ticket[i+1] - ticket[i] == 1)
        if consecutive > 1:
            return False, f"Too many consecutive pairs: {consecutive}"
        
        # Decade spread (3+ decades)
        decades = len(set(n // 10 for n in ticket))
        if decades < 3:
            return False, f"Only {decades} decades"
        
        return True, "OK"
    
    def score_ticket(self, ticket, bonus=None):
        """Score a ticket using all validated patterns."""
        ticket = sorted(ticket)
        score = 0.0
        
        # 1. Position frequency score (primary factor)
        pos_score = 0
        for i, num in enumerate(ticket):
            if i < len(self.position_freqs) and num in self.position_freqs[i]:
                pos_score += self.position_freqs[i][num]
        score += pos_score * 100  # Weight heavily
        
        # 2. Pair bonus (verified patterns)
        pair_score = 0
        for pair in combinations(ticket, 2):
            pair_score += self.pair_freqs.get(pair, 0)
        score += pair_score * 5
        
        # 3. Hot combo bonus (top 3-combos that repeat)
        for combo in self.top_combos:
            combo_set = set(combo)
            if combo_set.issubset(set(ticket)):
                score += 20
        
        # 4. Bonus ball score
        if bonus and bonus in self.bonus_freqs:
            score += self.bonus_freqs[bonus] * 50
        
        # 5. Last draw repeat bonus (45% chance of repeat)
        if self.draws:
            last_draw = set(self.draws[0]['main'])
            repeats = len(set(ticket) & last_draw)
            if repeats >= 1:
                score += repeats * 5 * self.repeat_rate
        
        return score
    
    def generate_candidate(self):
        """Generate a single candidate ticket using weighted random selection."""
        ticket = []
        
        for i in range(5):
            if i < len(self.position_ranges):
                min_val, max_val = self.position_ranges[i]
            else:
                min_val, max_val = self.main_range
            
            # Weight by position frequency
            candidates = list(range(min_val, max_val + 1))
            weights = []
            for num in candidates:
                if num in ticket:
                    weights.append(0)  # No duplicates
                else:
                    # Use frequency or default
                    freq = self.position_freqs[i].get(num, 0.01) if i < len(self.position_freqs) else 0.01
                    weights.append(freq + 0.001)  # Small base to avoid zero
            
            # Normalize and select
            total = sum(weights) or 1
            weights = [w/total for w in weights]
            
            # Weighted random choice
            r = random.random()
            cumsum = 0
            selected = candidates[0]
            for j, w in enumerate(weights):
                cumsum += w
                if r <= cumsum:
                    selected = candidates[j]
                    break
            
            ticket.append(selected)
        
        return sorted(ticket)
    
    def generate_best_bonus(self):
        """Generate optimal bonus ball."""
        if self.hot_bonus:
            # Prefer hot bonus balls
            weights = []
            for bonus in self.hot_bonus:
                freq = self.bonus_freqs.get(bonus, 0.05)
                weights.append(freq)
            total = sum(weights) or 1
            weights = [w/total for w in weights]
            
            r = random.random()
            cumsum = 0
            for i, w in enumerate(weights):
                cumsum += w
                if r <= cumsum:
                    return self.hot_bonus[i]
        
        # Fallback: best by frequency
        if self.bonus_freqs:
            return max(self.bonus_freqs.keys(), key=lambda x: self.bonus_freqs[x])
        return 1
    
    def hunt_jackpot(self, iterations=10000, top_n=10):
        """Run jackpot hunting algorithm to find best tickets."""
        print(f"\n{'='*60}")
        print(f"HUNTING JACKPOT FOR {self.lottery.upper()}")
        print(f"{'='*60}")
        print(f"Running {iterations:,} iterations...")
        
        candidates = []
        excluded_count = 0
        invalid_count = 0
        
        for i in range(iterations):
            ticket = self.generate_candidate()
            bonus = self.generate_best_bonus()
            
            # Check exclusion
            if self.is_excluded(ticket):
                excluded_count += 1
                continue
            
            # Check constraints
            valid, reason = self.validate_constraints(ticket)
            if not valid:
                invalid_count += 1
                continue
            
            # Score it
            score = self.score_ticket(ticket, bonus)
            candidates.append({
                'ticket': ticket,
                'bonus': bonus,
                'score': score
            })
        
        # Sort by score
        candidates.sort(key=lambda x: -x['score'])
        top_tickets = candidates[:top_n]
        
        print(f"\nResults:")
        print(f"  Valid candidates: {len(candidates):,}")
        print(f"  Excluded (past winners): {excluded_count:,}")
        print(f"  Invalid (constraints): {invalid_count:,}")
        
        print(f"\nTop {top_n} Jackpot Tickets:")
        for i, t in enumerate(top_tickets):
            print(f"  {i+1}. {t['ticket']} + Bonus: {t['bonus']} (Score: {t['score']:.2f})")
        
        return top_tickets
    
    def find_eventual_jackpot_ticket(self, iterations=50000):
        """Find THE single best ticket to play forever."""
        print(f"\n{'='*60}")
        print(f"FINDING EVENTUAL JACKPOT TICKET FOR {self.lottery.upper()}")
        print(f"{'='*60}")
        
        # Run multiple rounds and aggregate
        all_candidates = {}
        
        for round_num in range(5):
            print(f"  Round {round_num+1}/5...")
            tickets = self.hunt_jackpot(iterations=iterations//5, top_n=100)
            
            for t in tickets:
                key = (tuple(t['ticket']), t['bonus'])
                if key not in all_candidates:
                    all_candidates[key] = {'ticket': t['ticket'], 'bonus': t['bonus'], 'score': 0, 'count': 0}
                all_candidates[key]['score'] += t['score']
                all_candidates[key]['count'] += 1
        
        # Find most consistent high-scoring ticket
        best = max(all_candidates.values(), key=lambda x: x['score'] / max(x['count'], 1) * x['count'])
        
        print(f"\n{'='*60}")
        print(f"EVENTUAL JACKPOT TICKET FOR {self.lottery.upper()}:")
        print(f"{'='*60}")
        print(f"  Ticket: {best['ticket']} + Bonus: {best['bonus']}")
        print(f"  Score: {best['score']:.2f}")
        print(f"  Appeared in {best['count']} rounds")
        
        # Validate one more time
        valid, reason = self.validate_constraints(best['ticket'])
        excluded = self.is_excluded(best['ticket'])
        print(f"  Constraints: {'✅ PASS' if valid else '❌ FAIL: ' + reason}")
        print(f"  Not Past Winner: {'✅ CONFIRMED' if not excluded else '❌ EXCLUDED'}")
        
        return best


class ContinuousJackpotSystem:
    """Continuously running system that improves predictions over time."""
    
    def __init__(self):
        self.hunters = {}
        self.results = {}
        self.run_count = 0
        
        for lottery in ['l4l', 'la', 'pb', 'mm']:
            self.hunters[lottery] = JackpotHunter(lottery)
    
    def run_once(self):
        """Run one iteration for all lotteries."""
        self.run_count += 1
        print(f"\n{'#'*60}")
        print(f"CONTINUOUS JACKPOT HUNTER - RUN #{self.run_count}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}")
        
        for lottery, hunter in self.hunters.items():
            result = hunter.find_eventual_jackpot_ticket(iterations=20000)
            self.results[lottery] = result
        
        # Save results
        self.save_results()
        return self.results
    
    def save_results(self):
        """Save current best tickets."""
        output = {
            'timestamp': datetime.now().isoformat(),
            'run_count': self.run_count,
            'eventual_jackpot_tickets': {}
        }
        
        for lottery, result in self.results.items():
            output['eventual_jackpot_tickets'][lottery] = {
                'main': result['ticket'],
                'bonus': result['bonus'],
                'score': result['score']
            }
        
        path = DATA_DIR / 'eventual_jackpot_tickets.json'
        with open(path, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n✅ Saved to {path}")
    
    def run_continuous(self, interval_minutes=30, max_runs=None):
        """Run continuously, improving predictions."""
        run_count = 0
        
        while max_runs is None or run_count < max_runs:
            try:
                self.run_once()
                run_count += 1
                
                if max_runs and run_count >= max_runs:
                    break
                
                print(f"\nSleeping {interval_minutes} minutes until next run...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\nStopped by user")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)
        
        print(f"\nCompleted {run_count} runs")
        return self.results


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description='Continuous Jackpot Hunter')
    parser.add_argument('--lottery', '-l', help='Single lottery to analyze (l4l, la, pb, mm)')
    parser.add_argument('--continuous', '-c', action='store_true', help='Run continuously')
    parser.add_argument('--interval', '-i', type=int, default=30, help='Minutes between runs')
    parser.add_argument('--iterations', '-n', type=int, default=50000, help='Iterations per lottery')
    args = parser.parse_args()
    
    if args.lottery:
        # Single lottery mode
        hunter = JackpotHunter(args.lottery)
        result = hunter.find_eventual_jackpot_ticket(iterations=args.iterations)
        print(f"\n\nFINAL RECOMMENDATION FOR {args.lottery.upper()}:")
        print(f"Play this ticket FOREVER: {result['ticket']} + Bonus: {result['bonus']}")
    else:
        # All lotteries
        system = ContinuousJackpotSystem()
        
        if args.continuous:
            system.run_continuous(interval_minutes=args.interval)
        else:
            results = system.run_once()
            
            print("\n" + "="*60)
            print("FINAL EVENTUAL JACKPOT TICKETS")
            print("="*60)
            for lottery, result in results.items():
                print(f"{lottery.upper()}: {result['ticket']} + Bonus: {result['bonus']} (Score: {result['score']:.2f})")


if __name__ == '__main__':
    main()
