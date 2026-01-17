#!/usr/bin/env python3
"""
Prediction Tracker - Tracks wins, losses, and learns from lottery predictions.
Memorizes all predictions and compares against actual results.

Features:
- Track HOLD ticket hits per lottery
- Track pool selection coverage (could have won)
- Per-column accuracy tracking
- Win/loss history with patterns
- Automatic learning and improvement recommendations
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter

DATA_DIR = Path(__file__).parent / 'data'
TRACKER_FILE = DATA_DIR / 'prediction_memory.json'

# Our HOLD tickets (from daily_email_report.py)
HOLD_TICKETS = {
    'l4l': {'main': [1, 12, 30, 39, 47], 'bonus': 11},
    'la': {'main': [1, 15, 23, 42, 51], 'bonus': 4},
    'pb': {'main': [1, 11, 33, 52, 69], 'bonus': 20},
    'mm': {'main': [6, 10, 27, 42, 68], 'bonus': 24}
}

def load_tracker():
    """Load prediction tracking memory."""
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {
        'hold_tickets': HOLD_TICKETS,
        'results': {},  # date -> lottery -> result
        'hold_hits': {},  # lottery -> list of {date, matched, bonus_hit}
        'pool_hits': {},  # lottery -> list of {date, pool_matches, could_have_won}
        'column_accuracy': {},  # lottery -> {col_0: {correct: X, total: Y}, ...}
        'wins': [],  # List of actual wins
        'patterns': {},  # Learned patterns
        'total_plays': {},  # lottery -> count
        'created': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }

def save_tracker(tracker):
    """Save prediction tracking memory."""
    tracker['last_updated'] = datetime.now().isoformat()
    DATA_DIR.mkdir(exist_ok=True)
    with open(TRACKER_FILE, 'w') as f:
        json.dump(tracker, f, indent=2)

def check_hold_ticket(lottery, actual_draw, tracker):
    """Check how many numbers our HOLD ticket matched."""
    hold = HOLD_TICKETS.get(lottery, {})
    hold_main = set(hold.get('main', []))
    hold_bonus = hold.get('bonus')
    
    actual_main = set(actual_draw.get('main', []))
    actual_bonus = actual_draw.get('bonus')
    
    # Count matches
    main_matches = hold_main & actual_main
    bonus_hit = hold_bonus == actual_bonus
    
    return {
        'matched_count': len(main_matches),
        'matched_numbers': sorted(list(main_matches)),
        'bonus_hit': bonus_hit,
        'hold_ticket': hold,
        'actual_draw': actual_draw
    }

def check_pool_coverage(lottery, actual_draw, pools, tracker):
    """Check if our pool selections would have covered the winning numbers."""
    actual_main = actual_draw.get('main', [])
    actual_bonus = actual_draw.get('bonus')
    
    position_pools = pools.get('position_pools', [])
    bonus_pool = pools.get('bonus_pool', [])
    
    # Check each position
    covered = []
    for i, num in enumerate(sorted(actual_main)):
        if i < len(position_pools):
            if num in position_pools[i]:
                covered.append(num)
    
    bonus_covered = actual_bonus in bonus_pool if bonus_pool else False
    
    # Could have won = all 5 main numbers were in their respective pools
    could_have_won = len(covered) == 5 and bonus_covered
    
    return {
        'covered_count': len(covered),
        'covered_numbers': covered,
        'bonus_covered': bonus_covered,
        'could_have_won': could_have_won,
        'pools': pools
    }

def update_column_accuracy(lottery, actual_draw, pools, tracker):
    """Track per-column prediction accuracy."""
    if lottery not in tracker['column_accuracy']:
        tracker['column_accuracy'][lottery] = {}
    
    actual_main = sorted(actual_draw.get('main', []))
    position_pools = pools.get('position_pools', [])
    
    for i, num in enumerate(actual_main):
        col_key = f'position_{i+1}'
        if col_key not in tracker['column_accuracy'][lottery]:
            tracker['column_accuracy'][lottery][col_key] = {'correct': 0, 'total': 0}
        
        tracker['column_accuracy'][lottery][col_key]['total'] += 1
        
        if i < len(position_pools) and num in position_pools[i]:
            tracker['column_accuracy'][lottery][col_key]['correct'] += 1

def record_result(lottery, draw_date, actual_draw, pools, tracker):
    """Record a drawing result and check predictions."""
    # Store result
    if draw_date not in tracker['results']:
        tracker['results'][draw_date] = {}
    tracker['results'][draw_date][lottery] = actual_draw
    
    # Check HOLD ticket
    hold_result = check_hold_ticket(lottery, actual_draw, tracker)
    if lottery not in tracker['hold_hits']:
        tracker['hold_hits'][lottery] = []
    tracker['hold_hits'][lottery].append({
        'date': draw_date,
        'matched': hold_result['matched_count'],
        'matched_numbers': hold_result['matched_numbers'],
        'bonus_hit': hold_result['bonus_hit']
    })
    
    # Check pool coverage
    pool_result = check_pool_coverage(lottery, actual_draw, pools, tracker)
    if lottery not in tracker['pool_hits']:
        tracker['pool_hits'][lottery] = []
    tracker['pool_hits'][lottery].append({
        'date': draw_date,
        'covered': pool_result['covered_count'],
        'could_have_won': pool_result['could_have_won']
    })
    
    # Update column accuracy
    update_column_accuracy(lottery, actual_draw, pools, tracker)
    
    # Track total plays
    if lottery not in tracker['total_plays']:
        tracker['total_plays'][lottery] = 0
    tracker['total_plays'][lottery] += 1
    
    # Check for wins (3+ matches or jackpot)
    if hold_result['matched_count'] >= 3:
        win_record = {
            'date': draw_date,
            'lottery': lottery,
            'type': 'HOLD',
            'matched': hold_result['matched_count'],
            'bonus_hit': hold_result['bonus_hit'],
            'prize_tier': get_prize_tier(lottery, hold_result['matched_count'], hold_result['bonus_hit'])
        }
        tracker['wins'].append(win_record)
    
    return hold_result, pool_result

def get_prize_tier(lottery, matched, bonus_hit):
    """Get prize tier description."""
    if matched == 5 and bonus_hit:
        return 'JACKPOT!'
    elif matched == 5:
        return '5/5 (No Bonus)'
    elif matched == 4 and bonus_hit:
        return '4/5 + Bonus'
    elif matched == 4:
        return '4/5'
    elif matched == 3 and bonus_hit:
        return '3/5 + Bonus'
    elif matched == 3:
        return '3/5'
    return f'{matched}/5'

def get_stats_summary(tracker):
    """Generate statistics summary for email."""
    summary = []
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        if lottery not in tracker['hold_hits']:
            continue
        
        hits = tracker['hold_hits'][lottery]
        if not hits:
            continue
        
        total = len(hits)
        match_counts = Counter([h['matched'] for h in hits])
        bonus_hits = sum(1 for h in hits if h['bonus_hit'])
        
        # Calculate best hit ever
        best_hit = max(hits, key=lambda x: (x['matched'], x['bonus_hit']))
        
        # Column accuracy
        col_acc = tracker.get('column_accuracy', {}).get(lottery, {})
        col_stats = []
        for i in range(5):
            col_key = f'position_{i+1}'
            if col_key in col_acc:
                c = col_acc[col_key]
                rate = (c['correct'] / c['total'] * 100) if c['total'] > 0 else 0
                col_stats.append(f"P{i+1}: {rate:.1f}%")
        
        lottery_summary = {
            'lottery': lottery.upper(),
            'total_draws': total,
            'match_distribution': dict(match_counts),
            'bonus_hits': bonus_hits,
            'best_hit': f"{best_hit['matched']}/5" + (" + Bonus!" if best_hit['bonus_hit'] else ""),
            'best_hit_date': best_hit['date'],
            'column_accuracy': col_stats
        }
        summary.append(lottery_summary)
    
    return summary

def get_wins_report(tracker):
    """Get recent wins for email."""
    wins = tracker.get('wins', [])
    # Return last 10 wins
    return sorted(wins, key=lambda x: x['date'], reverse=True)[:10]

def get_could_have_won_report(tracker):
    """Check times when pool selections could have won jackpot."""
    could_haves = []
    for lottery, hits in tracker.get('pool_hits', {}).items():
        for hit in hits:
            if hit.get('could_have_won'):
                could_haves.append({
                    'lottery': lottery.upper(),
                    'date': hit['date']
                })
    return sorted(could_haves, key=lambda x: x['date'], reverse=True)[:10]

def generate_email_section(tracker):
    """Generate tracking section for family email."""
    stats = get_stats_summary(tracker)
    wins = get_wins_report(tracker)
    could_haves = get_could_have_won_report(tracker)
    
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("📊 PREDICTION TRACKING & LEARNING SYSTEM")
    lines.append("=" * 60)
    
    # Stats per lottery
    for s in stats:
        lines.append(f"\n🎰 {s['lottery']}")
        lines.append(f"   Total Draws Tracked: {s['total_draws']}")
        lines.append(f"   Best Hit Ever: {s['best_hit']} on {s['best_hit_date']}")
        lines.append(f"   Match Distribution: {s['match_distribution']}")
        lines.append(f"   Bonus Ball Hits: {s['bonus_hits']}")
        if s['column_accuracy']:
            lines.append(f"   Column Accuracy: {' | '.join(s['column_accuracy'])}")
    
    # Recent wins
    if wins:
        lines.append("\n🏆 RECENT WINS (3+ matches):")
        for w in wins[:5]:
            lines.append(f"   {w['date']} {w['lottery']}: {w['prize_tier']}")
    
    # Could have won with pools
    if could_haves:
        lines.append("\n💡 POOL COVERAGE - Could Have Won:")
        for c in could_haves[:5]:
            lines.append(f"   {c['date']} {c['lottery']}: All 5 + bonus in pools!")
    
    # Learning insights
    lines.append("\n📚 LEARNING INSIGHTS:")
    total_tracked = sum(s['total_draws'] for s in stats)
    if total_tracked > 0:
        lines.append(f"   • Total draws tracked: {total_tracked}")
        lines.append(f"   • Total wins recorded: {len(wins)}")
        
        # Best performing lottery
        best_lottery = max(stats, key=lambda x: sum(k*v for k,v in x['match_distribution'].items()))
        lines.append(f"   • Best performing: {best_lottery['lottery']}")
    
    return '\n'.join(lines)

# Export for use in daily_email_report.py
if __name__ == '__main__':
    # Test the tracker
    tracker = load_tracker()
    print("Prediction Tracker loaded!")
    print(f"Total results tracked: {len(tracker.get('results', {}))}")
    print(f"Wins recorded: {len(tracker.get('wins', []))}")
    
    # Generate sample report
    print(generate_email_section(tracker))
    
    save_tracker(tracker)
    print(f"\nTracker saved to: {TRACKER_FILE}")
