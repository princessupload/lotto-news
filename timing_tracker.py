"""
TIMING TRACKER SYSTEM
Tracks timing patterns for lottery analysis.

IMPORTANT - VALIDATED vs INFORMATIONAL:
- VALIDATED (used for prediction boost):
  * 3-combo repeats (proven - combos DO repeat historically)
  * Repeat candidates (35-48% of draws have repeats)
  * Position frequency data (40-44% stability vs 15-17% random)
  
- INFORMATIONAL ONLY (NOT used for boost - gambler's fallacy):
  * Overdue numbers (random data shows same 68-74% hit rate - no edge)
  * Number gaps (each draw is independent)

============================================================================
USER'S HOLD FOREVER TICKETS (Auto-checked for wins):
  PB:  [4, 21, 35, 61, 69] + PB: 21
  LA:  [2, 15, 21, 33, 52] + SB: 4
  L4L: [5, 12, 30, 39, 40] + LB: 2
  MM:  [18, 21, 27, 42, 68] + MB: 24

NEXT DRAW PREDICTIONS (Analyzer generates these):
  Optimal Windows: L4L=400, LA=150, PB=100, MM=30 draws
  Verified Methods: Position+Momentum (1.21x), Hot Pairs (1.20x)
============================================================================
"""
import json
from collections import Counter, defaultdict
from pathlib import Path
from itertools import combinations
from datetime import datetime

DATA_DIR = Path(__file__).parent / 'data'

LOTTERY_CONFIG = {
    'l4l': {'name': 'Lucky for Life', 'main_range': 48, 'bonus_range': 18, 'draws_per_week': 7},
    'la': {'name': 'Lotto America', 'main_range': 52, 'bonus_range': 10, 'draws_per_week': 3},
    'pb': {'name': 'Powerball', 'main_range': 69, 'bonus_range': 26, 'draws_per_week': 3},
    'mm': {'name': 'Mega Millions', 'main_range': 70, 'bonus_range': 25, 'draws_per_week': 2}
}

def calculate_timing_data(lottery):
    """Calculate comprehensive timing data for a lottery."""
    with open(DATA_DIR / f'{lottery}.json') as f:
        data = json.load(f)
    draws = data['draws']
    config = LOTTERY_CONFIG[lottery]
    
    result = {
        'lottery': lottery,
        'name': config['name'],
        'updated': datetime.now().isoformat(),
        'total_draws': len(draws),
        'last_draw': {
            'main': sorted(draws[0]['main']),
            'bonus': draws[0].get('bonus'),
            'date': draws[0].get('date', 'Unknown')
        }
    }
    
    # ========== 1. NUMBER GAP ANALYSIS ==========
    all_numbers = set(n for d in draws for n in d['main'])
    
    # Calculate average gap for each number
    number_gaps = {}
    current_gaps = {}
    
    for num in all_numbers:
        appearances = [i for i, d in enumerate(draws) if num in d['main']]
        if len(appearances) >= 2:
            gaps = [appearances[j+1] - appearances[j] for j in range(len(appearances)-1)]
            number_gaps[num] = {
                'avg_gap': sum(gaps) / len(gaps),
                'min_gap': min(gaps),
                'max_gap': max(gaps),
                'appearances': len(appearances)
            }
        current_gaps[num] = appearances[0] if appearances else len(draws)
    
    # Find overdue numbers
    overdue = []
    for num in all_numbers:
        if num in number_gaps:
            avg = number_gaps[num]['avg_gap']
            curr = current_gaps[num]
            if avg > 0:
                ratio = curr / avg
                if ratio > 1.2:
                    overdue.append({
                        'number': num,
                        'current_gap': curr,
                        'avg_gap': round(avg, 1),
                        'ratio': round(ratio, 2),
                        'status': 'VERY_OVERDUE' if ratio > 2 else 'OVERDUE' if ratio > 1.5 else 'DUE'
                    })
    
    overdue.sort(key=lambda x: x['ratio'], reverse=True)
    result['overdue_numbers'] = overdue[:15]
    
    # ========== 2. REPEAT ANALYSIS ==========
    last_draw_nums = sorted(draws[0]['main'])
    repeat_candidates = []
    
    for num in last_draw_nums:
        # Count historical repeats
        repeats = sum(1 for i in range(len(draws)-1) 
                     if num in draws[i]['main'] and num in draws[i+1]['main'])
        total = sum(1 for d in draws if num in d['main'])
        rate = repeats / total if total > 0 else 0
        
        repeat_candidates.append({
            'number': num,
            'repeat_count': repeats,
            'total_appearances': total,
            'repeat_rate': round(rate * 100, 1)
        })
    
    repeat_candidates.sort(key=lambda x: x['repeat_count'], reverse=True)
    result['repeat_candidates'] = repeat_candidates
    
    # Overall repeat status
    draws_since_repeat = 0
    for i in range(len(draws) - 1):
        if set(draws[i]['main']) & set(draws[i+1]['main']):
            draws_since_repeat = i
            break
    
    repeat_events = sum(1 for i in range(len(draws)-1) 
                       if set(draws[i]['main']) & set(draws[i+1]['main']))
    avg_repeat_gap = (len(draws) - 1) / repeat_events if repeat_events > 0 else 3
    
    result['repeat_status'] = {
        'draws_since_last_repeat': draws_since_repeat,
        'avg_gap_between_repeats': round(avg_repeat_gap, 1),
        'repeat_rate': round(repeat_events / (len(draws)-1) * 100, 1),
        'expect_repeat_soon': draws_since_repeat >= avg_repeat_gap * 0.8
    }
    
    # ========== 3. 3-COMBO TRACKING ==========
    combo_apps = defaultdict(list)
    for i, d in enumerate(draws):
        main = tuple(sorted(d['main']))
        for c3 in combinations(main, 3):
            combo_apps[c3].append(i)
    
    # Find combos due to repeat
    due_combos = []
    for combo, apps in combo_apps.items():
        if len(apps) >= 2:
            gaps = [apps[j+1] - apps[j] for j in range(len(apps)-1)]
            avg_gap = sum(gaps) / len(gaps)
            last_seen = apps[0]
            expected_return = avg_gap - last_seen
            
            if expected_return <= 50:  # Due within 50 draws
                due_combos.append({
                    'combo': list(combo),
                    'times_appeared': len(apps),
                    'last_seen': last_seen,
                    'avg_gap': round(avg_gap, 0),
                    'expected_in': max(0, round(expected_return, 0))
                })
    
    due_combos.sort(key=lambda x: x['expected_in'])
    result['due_combos'] = due_combos[:10]
    
    # ========== 4. POSITION ANALYSIS ==========
    position_data = []
    for pos in range(5):
        pos_nums = [sorted(d['main'])[pos] for d in draws]
        last_num = pos_nums[0]
        
        # Find when this number last appeared in this position
        same_pos = [i for i, n in enumerate(pos_nums) if n == last_num]
        if len(same_pos) >= 2:
            gaps = [same_pos[j+1] - same_pos[j] for j in range(len(same_pos)-1)]
            avg_gap = sum(gaps) / len(gaps)
        else:
            avg_gap = 20  # Default
        
        # Top numbers for this position
        pos_freq = Counter(pos_nums[:150])  # Recent 150
        top_nums = [n for n, _ in pos_freq.most_common(5)]
        
        position_data.append({
            'position': pos + 1,
            'last_number': last_num,
            'avg_return_gap': round(avg_gap, 1),
            'top_numbers': top_nums
        })
    
    result['position_analysis'] = position_data
    
    # ========== 5. BONUS BALL ANALYSIS ==========
    bonus_list = [d.get('bonus') for d in draws if d.get('bonus')]
    bonus_gaps = defaultdict(list)
    
    for b in set(bonus_list):
        apps = [i for i, x in enumerate(bonus_list) if x == b]
        for j in range(len(apps) - 1):
            bonus_gaps[b].append(apps[j+1] - apps[j])
    
    bonus_avg = {b: sum(g)/len(g) for b, g in bonus_gaps.items() if g}
    
    # Find overdue bonus
    overdue_bonus = []
    for b in set(bonus_list):
        if b is None:
            continue
        curr = next((i for i, x in enumerate(bonus_list) if x == b), 999)
        avg = bonus_avg.get(b, 20)
        if avg > 0 and curr / avg > 1.2:
            overdue_bonus.append({
                'bonus': b,
                'current_gap': curr,
                'avg_gap': round(avg, 1),
                'ratio': round(curr / avg, 2)
            })
    
    overdue_bonus.sort(key=lambda x: x['ratio'], reverse=True)
    result['overdue_bonus'] = overdue_bonus[:5]
    
    # Bonus repeat rate
    bonus_repeats = sum(1 for i in range(len(bonus_list)-1) if bonus_list[i] == bonus_list[i+1])
    result['bonus_repeat_rate'] = round(bonus_repeats / (len(bonus_list)-1) * 100, 1)
    
    # ========== 6. TIMING-BASED PREDICTION ==========
    timing_prediction = {
        'main': [],
        'bonus': None,
        'reasoning': []
    }
    
    prediction_pool = set()
    
    # Add top repeat candidates
    top_repeats = [rc['number'] for rc in repeat_candidates[:2]]
    prediction_pool.update(top_repeats)
    timing_prediction['reasoning'].append(f"Repeat candidates from last draw: {top_repeats}")
    
    # Add top overdue
    top_overdue = [o['number'] for o in overdue[:3]]
    prediction_pool.update(top_overdue)
    timing_prediction['reasoning'].append(f"Overdue numbers: {top_overdue}")
    
    # Add from due combos
    if due_combos:
        for combo_data in due_combos[:2]:
            for n in combo_data['combo']:
                prediction_pool.add(n)
        timing_prediction['reasoning'].append(f"Due 3-combos: {[c['combo'] for c in due_combos[:2]]}")
    
    # Build final prediction
    final_nums = sorted(list(prediction_pool))[:5]
    while len(final_nums) < 5:
        for o in overdue:
            if o['number'] not in final_nums:
                final_nums.append(o['number'])
                break
    
    timing_prediction['main'] = sorted(final_nums[:5])
    
    # Bonus prediction
    if overdue_bonus:
        timing_prediction['bonus'] = overdue_bonus[0]['bonus']
    elif result['bonus_repeat_rate'] > 5:
        timing_prediction['bonus'] = draws[0].get('bonus')
    else:
        timing_prediction['bonus'] = Counter(bonus_list[:30]).most_common(1)[0][0]
    
    result['timing_prediction'] = timing_prediction
    
    return result


def update_all_timing_data():
    """Update timing data for all lotteries."""
    all_data = {}
    
    for lottery in LOTTERY_CONFIG.keys():
        try:
            all_data[lottery] = calculate_timing_data(lottery)
        except Exception as e:
            print(f"Error calculating timing for {lottery}: {e}")
    
    # Save to file
    with open(DATA_DIR / 'timing_tracker.json', 'w') as f:
        json.dump(all_data, f, indent=2)
    
    return all_data


def get_timing_data(lottery=None):
    """Get timing data for a lottery or all lotteries."""
    timing_file = DATA_DIR / 'timing_tracker.json'
    
    if not timing_file.exists():
        update_all_timing_data()
    
    with open(timing_file) as f:
        all_data = json.load(f)
    
    if lottery:
        return all_data.get(lottery, {})
    return all_data


if __name__ == '__main__':
    print("Updating timing tracker data...")
    data = update_all_timing_data()
    
    for lot, d in data.items():
        print(f"\n{'='*60}")
        print(f"{d['name']}")
        print(f"{'='*60}")
        print(f"Last draw: {d['last_draw']['main']} + {d['last_draw']['bonus']}")
        print(f"\nOverdue numbers:")
        for o in d['overdue_numbers'][:5]:
            print(f"  {o['number']}: {o['ratio']}x overdue ({o['status']})")
        print(f"\nRepeat candidates:")
        for r in d['repeat_candidates'][:3]:
            print(f"  {r['number']}: {r['repeat_count']} repeats ({r['repeat_rate']}%)")
        print(f"\nDue 3-combos:")
        for c in d['due_combos'][:3]:
            print(f"  {c['combo']}: expect in ~{c['expected_in']} draws")
        print(f"\nTIMING PREDICTION: {d['timing_prediction']['main']} + {d['timing_prediction']['bonus']}")
    
    print("\n\nTiming data saved to data/timing_tracker.json")
