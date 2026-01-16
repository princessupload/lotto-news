"""
PREDICTION TRACKING SYSTEM
Tracks AI predictions vs actual results for all 4 lotteries.
Learns from what works and adjusts prediction weights accordingly.
"""
import json
from datetime import datetime
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent / 'data'
HISTORY_FILE = DATA_DIR / 'prediction_history.json'
POOL_ACCURACY_FILE = DATA_DIR / 'pool_accuracy.json'

def load_history():
    """Load prediction history."""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {
        "predictions": [],
        "results": {
            "l4l": {"5_5": 0, "4_5": 0, "3_5": 0, "2_5": 0, "1_5": 0, "0_5": 0, "bonus_hits": 0, "total": 0},
            "la": {"5_5": 0, "4_5": 0, "3_5": 0, "2_5": 0, "1_5": 0, "0_5": 0, "bonus_hits": 0, "total": 0},
            "pb": {"5_5": 0, "4_5": 0, "3_5": 0, "2_5": 0, "1_5": 0, "0_5": 0, "bonus_hits": 0, "total": 0},
            "mm": {"5_5": 0, "4_5": 0, "3_5": 0, "2_5": 0, "1_5": 0, "0_5": 0, "bonus_hits": 0, "total": 0}
        },
        "method_performance": {
            "l4l": {"position_freq": 0, "recency": 0, "pairs": 0, "near_hit": 0, "trend": 0},
            "la": {"position_freq": 0, "recency": 0, "pairs": 0, "near_hit": 0, "trend": 0},
            "pb": {"position_freq": 0, "recency": 0, "pairs": 0, "near_hit": 0, "trend": 0},
            "mm": {"position_freq": 0, "recency": 0, "pairs": 0, "near_hit": 0, "trend": 0}
        },
        "learned_weights": {
            "l4l": {"position_freq": 5, "recency": 2, "pairs": 3, "near_hit": 1, "trend": 2},
            "la": {"position_freq": 5, "recency": 2, "pairs": 3, "near_hit": 1, "trend": 2},
            "pb": {"position_freq": 5, "recency": 2, "pairs": 3, "near_hit": 1, "trend": 2},
            "mm": {"position_freq": 5, "recency": 2, "pairs": 3, "near_hit": 1, "trend": 2}
        },
        "lastUpdated": None
    }

def save_history(history):
    """Save prediction history."""
    history['lastUpdated'] = datetime.now().isoformat()
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def store_prediction(lottery, prediction, target_date, method_scores=None):
    """Store a prediction before the draw happens."""
    history = load_history()
    
    # Check if we already have a prediction for this lottery and date
    for p in history['predictions']:
        if p['lottery'] == lottery and p['target_date'] == target_date and p['status'] == 'pending':
            # Update existing prediction
            p['main'] = prediction['main']
            p['bonus'] = prediction['bonus']
            p['method_scores'] = method_scores or {}
            p['updated_at'] = datetime.now().isoformat()
            save_history(history)
            return p
    
    # Create new prediction entry
    entry = {
        'id': len(history['predictions']) + 1,
        'lottery': lottery,
        'target_date': target_date,
        'main': prediction['main'],
        'bonus': prediction['bonus'],
        'method_scores': method_scores or {},
        'created_at': datetime.now().isoformat(),
        'status': 'pending',
        'actual_main': None,
        'actual_bonus': None,
        'main_matches': None,
        'bonus_match': None,
        'checked_at': None
    }
    
    history['predictions'].append(entry)
    save_history(history)
    return entry

def check_prediction(lottery, actual_main, actual_bonus):
    """Check pending predictions against actual results."""
    history = load_history()
    checked = []
    
    for pred in history['predictions']:
        if pred['lottery'] == lottery and pred['status'] == 'pending':
            # Compare prediction to actual
            pred_set = set(pred['main'])
            actual_set = set(actual_main)
            matches = pred_set & actual_set
            match_count = len(matches)
            bonus_match = pred['bonus'] == actual_bonus
            
            # Update prediction entry
            pred['actual_main'] = actual_main
            pred['actual_bonus'] = actual_bonus
            pred['main_matches'] = list(matches)
            pred['match_count'] = match_count
            pred['bonus_match'] = bonus_match
            pred['status'] = 'checked'
            pred['checked_at'] = datetime.now().isoformat()
            
            # Update results tally
            key = f"{match_count}_5"
            history['results'][lottery][key] += 1
            history['results'][lottery]['total'] += 1
            if bonus_match:
                history['results'][lottery]['bonus_hits'] += 1
            
            # Update method performance based on which numbers hit
            if pred.get('method_scores'):
                for num in matches:
                    for method, nums in pred['method_scores'].items():
                        if num in nums:
                            history['method_performance'][lottery][method] += 1
            
            checked.append({
                'prediction': pred['main'],
                'actual': actual_main,
                'matches': match_count,
                'matched_numbers': list(matches),
                'bonus_predicted': pred['bonus'],
                'bonus_actual': actual_bonus,
                'bonus_hit': bonus_match
            })
    
    # Learn and adjust weights based on performance
    if checked:
        _adjust_weights(history, lottery)
    
    save_history(history)
    return checked

def _adjust_weights(history, lottery):
    """Adjust prediction method weights based on what's working."""
    perf = history['method_performance'][lottery]
    weights = history['learned_weights'][lottery]
    
    # Find best and worst performing methods
    if sum(perf.values()) > 0:
        total = sum(perf.values())
        for method in perf:
            # Calculate relative performance
            method_pct = perf[method] / total if total > 0 else 0.2
            
            # Adjust weight: boost methods that hit more often
            if method_pct > 0.25:  # Above average
                weights[method] = min(10, weights[method] + 1)
            elif method_pct < 0.15:  # Below average
                weights[method] = max(1, weights[method] - 1)

def get_learned_weights(lottery):
    """Get the learned weights for a lottery."""
    history = load_history()
    return history.get('learned_weights', {}).get(lottery, {
        'position_freq': 5, 'recency': 2, 'pairs': 3, 'near_hit': 1, 'trend': 2
    })

def get_performance_summary():
    """Get summary of prediction performance."""
    history = load_history()
    summary = {}
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        results = history['results'][lottery]
        total = results['total']
        
        if total > 0:
            summary[lottery] = {
                'total_predictions': total,
                'hit_rates': {
                    '5/5': results['5_5'],
                    '4/5': results['4_5'],
                    '3/5': results['3_5'],
                    '2/5': results['2_5'],
                    '1/5': results['1_5'],
                    '0/5': results['0_5']
                },
                'bonus_hit_rate': f"{results['bonus_hits']}/{total} ({results['bonus_hits']/total*100:.1f}%)",
                '3_plus_rate': f"{(results['3_5']+results['4_5']+results['5_5'])/total*100:.1f}%",
                'avg_matches': (
                    5*results['5_5'] + 4*results['4_5'] + 3*results['3_5'] + 
                    2*results['2_5'] + 1*results['1_5']
                ) / total,
                'learned_weights': history['learned_weights'][lottery],
                'method_hits': history['method_performance'][lottery]
            }
        else:
            summary[lottery] = {
                'total_predictions': 0,
                'message': 'No predictions tracked yet'
            }
    
    return summary

def get_pending_predictions():
    """Get all pending predictions."""
    history = load_history()
    return [p for p in history['predictions'] if p['status'] == 'pending']

def load_pool_accuracy():
    """Load pool accuracy tracking data."""
    if POOL_ACCURACY_FILE.exists():
        with open(POOL_ACCURACY_FILE) as f:
            return json.load(f)
    return {"tracking_started": datetime.now().strftime('%Y-%m-%d'), "lotteries": {}}

def save_pool_accuracy(data):
    """Save pool accuracy tracking data."""
    with open(POOL_ACCURACY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_position_pools(draws, pool_size=8):
    """Generate position pools from historical draws."""
    if not draws:
        return [list(range(1, pool_size+1)) for _ in range(5)]
    position_freq = [Counter() for _ in range(5)]
    for draw in draws:
        main = sorted(draw.get('main', []))
        for pos, num in enumerate(main):
            if pos < 5:
                position_freq[pos][num] += 1
    pools = []
    for pos in range(5):
        top_nums = [n for n, _ in position_freq[pos].most_common(pool_size)]
        pools.append(sorted(top_nums) if top_nums else list(range(1, pool_size+1)))
    return pools

def check_pool_accuracy(lottery, actual_draw):
    """Check how well our pools predicted the actual draw."""
    # Load draws WITHOUT the latest one (what we would have had before)
    data_file = DATA_DIR / f'{lottery}.json'
    if not data_file.exists():
        return None
    
    with open(data_file) as f:
        data = json.load(f)
    
    draws = data.get('draws', [])
    if len(draws) < 2:
        return None
    
    # Get pools that WOULD have been generated before this draw
    old_draws = draws[1:]  # Exclude latest draw
    pools = get_position_pools(old_draws)
    
    # Get bonus pool (top 6 hot bonus numbers)
    bonus_freq = Counter(d.get('bonus') for d in old_draws[:50] if d.get('bonus'))
    bonus_pool = [n for n, _ in bonus_freq.most_common(6)]
    
    # Load accuracy data
    accuracy = load_pool_accuracy()
    
    if lottery not in accuracy.get('lotteries', {}):
        accuracy['lotteries'][lottery] = {
            "total_draws_tracked": 0,
            "position_hits": [0, 0, 0, 0, 0],
            "position_attempts": [0, 0, 0, 0, 0],
            "bonus_hits": 0,
            "bonus_attempts": 0,
            "potential_jackpots": 0,
            "partial_matches": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0, "0": 0},
            "history": []
        }
    
    lot_data = accuracy['lotteries'][lottery]
    actual_main = sorted(actual_draw.get('main', []))
    actual_bonus = actual_draw.get('bonus')
    
    # Check each position
    position_hits = []
    for i, (pool, actual_num) in enumerate(zip(pools, actual_main)):
        hit = actual_num in pool
        position_hits.append(hit)
        lot_data['position_attempts'][i] += 1
        if hit:
            lot_data['position_hits'][i] += 1
    
    # Check bonus
    bonus_hit = actual_bonus in bonus_pool if bonus_pool and actual_bonus else False
    lot_data['bonus_attempts'] += 1
    if bonus_hit:
        lot_data['bonus_hits'] += 1
    
    # Count total hits
    total_hits = sum(position_hits)
    lot_data['partial_matches'][str(total_hits)] += 1
    
    # Check for potential jackpot
    if total_hits == 5 and bonus_hit:
        lot_data['potential_jackpots'] += 1
    
    lot_data['total_draws_tracked'] += 1
    
    # Add to history (keep last 50)
    lot_data['history'].append({
        'date': actual_draw.get('date', ''),
        'actual': actual_main,
        'bonus': actual_bonus,
        'hits': total_hits,
        'bonus_hit': bonus_hit,
        'position_hits': position_hits
    })
    lot_data['history'] = lot_data['history'][-50:]
    
    save_pool_accuracy(accuracy)
    
    return {
        'hits': total_hits,
        'bonus_hit': bonus_hit,
        'position_hits': position_hits
    }

def auto_check_predictions():
    """Automatically check pending predictions against latest draw data."""
    from pathlib import Path
    import json
    
    history = load_history()
    checked_count = 0
    pool_checks = 0
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        # Load latest draw
        data_file = DATA_DIR / f'{lottery}.json'
        if not data_file.exists():
            continue
        
        with open(data_file) as f:
            data = json.load(f)
        
        if not data.get('draws'):
            continue
        
        latest = data['draws'][0]
        latest_date = latest.get('date')
        
        # Check pool accuracy for this lottery
        accuracy = load_pool_accuracy()
        lot_accuracy = accuracy.get('lotteries', {}).get(lottery, {})
        history_dates = [h.get('date') for h in lot_accuracy.get('history', [])]
        
        # Only check if we haven't already tracked this draw
        if latest_date not in history_dates:
            result = check_pool_accuracy(lottery, latest)
            if result:
                pool_checks += 1
                print(f"Pool accuracy for {lottery} on {latest_date}: {result['hits']}/5 positions hit")
        
        # Check any pending predictions for this lottery
        for pred in history['predictions']:
            if pred['lottery'] == lottery and pred['status'] == 'pending':
                # If the target date matches or has passed
                if pred['target_date'] <= latest_date:
                    result = check_prediction(lottery, latest['main'], latest['bonus'])
                    if result:
                        checked_count += 1
    
    return {'predictions_checked': checked_count, 'pool_accuracy_checks': pool_checks}

if __name__ == '__main__':
    print("="*60)
    print("PREDICTION TRACKING SYSTEM")
    print("="*60)
    
    # Show current performance
    summary = get_performance_summary()
    
    for lottery, data in summary.items():
        print(f"\n{lottery.upper()}:")
        if data['total_predictions'] > 0:
            print(f"  Total predictions: {data['total_predictions']}")
            print(f"  Hit rates: {data['hit_rates']}")
            print(f"  Bonus hits: {data['bonus_hit_rate']}")
            print(f"  3+ match rate: {data['3_plus_rate']}")
            print(f"  Avg matches: {data['avg_matches']:.2f}")
            print(f"  Learned weights: {data['learned_weights']}")
        else:
            print(f"  {data['message']}")
    
    # Show pending predictions
    pending = get_pending_predictions()
    if pending:
        print(f"\nPending predictions: {len(pending)}")
        for p in pending:
            print(f"  {p['lottery'].upper()}: {p['main']} +{p['bonus']} for {p['target_date']}")
