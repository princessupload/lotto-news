"""
MORNING EVALUATION ROUTINE
Run every morning to:
1. Check if new draw data is available
2. Compare predictions to actual results
3. Store findings permanently
4. Update learned weights
5. Generate new predictions for upcoming draws

Best run after 8 AM CT when all lottery sites have updated.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))
from prediction_tracking import (
    load_history, save_history, store_prediction, check_prediction,
    get_performance_summary, get_pending_predictions, get_learned_weights
)

DATA_DIR = Path(__file__).parent / 'data'
FINDINGS_FILE = DATA_DIR / 'permanent_findings.json'

def load_findings():
    """Load permanent findings database."""
    if FINDINGS_FILE.exists():
        with open(FINDINGS_FILE) as f:
            return json.load(f)
    return {
        'patterns': {},
        'insights': [],
        'daily_logs': [],
        'last_evaluation': None
    }

def save_findings(findings):
    """Save permanent findings."""
    with open(FINDINGS_FILE, 'w') as f:
        json.dump(findings, f, indent=2)

def get_latest_draw(lottery):
    """Get the most recent draw for a lottery."""
    data_file = DATA_DIR / f'{lottery}.json'
    if not data_file.exists():
        return None
    with open(data_file) as f:
        data = json.load(f)
    if data.get('draws'):
        return data['draws'][0]
    return None

def evaluate_predictions():
    """Check all pending predictions against latest draws."""
    print("\n" + "="*70)
    print("CHECKING PENDING PREDICTIONS")
    print("="*70)
    
    history = load_history()
    results = []
    
    for pred in history['predictions']:
        if pred['status'] != 'pending':
            continue
        
        lottery = pred['lottery']
        target_date = pred['target_date']
        
        # Get latest draw
        latest = get_latest_draw(lottery)
        if not latest:
            continue
        
        latest_date = latest.get('date')
        
        # Check if this draw matches our prediction target
        if latest_date and latest_date >= target_date:
            actual_main = latest['main']
            actual_bonus = latest['bonus']
            pred_main = set(pred['main'])
            
            # Calculate matches
            matches = pred_main & set(actual_main)
            match_count = len(matches)
            bonus_hit = pred['bonus'] == actual_bonus
            
            # Update prediction
            pred['actual_main'] = actual_main
            pred['actual_bonus'] = actual_bonus
            pred['main_matches'] = list(matches)
            pred['match_count'] = match_count
            pred['bonus_match'] = bonus_hit
            pred['status'] = 'checked'
            pred['checked_at'] = datetime.now().isoformat()
            
            # Update results tally
            key = f"{match_count}_5"
            history['results'][lottery][key] = history['results'][lottery].get(key, 0) + 1
            history['results'][lottery]['total'] = history['results'][lottery].get('total', 0) + 1
            if bonus_hit:
                history['results'][lottery]['bonus_hits'] = history['results'][lottery].get('bonus_hits', 0) + 1
            
            # Track method performance
            if pred.get('method_scores'):
                for method, nums in pred['method_scores'].items():
                    for num in matches:
                        if num in nums:
                            if method not in history['method_performance'][lottery]:
                                history['method_performance'][lottery][method] = 0
                            history['method_performance'][lottery][method] += 1
            
            result = {
                'lottery': lottery.upper(),
                'target_date': target_date,
                'predicted': pred['main'],
                'actual': actual_main,
                'matches': match_count,
                'matched_nums': list(matches),
                'bonus_predicted': pred['bonus'],
                'bonus_actual': actual_bonus,
                'bonus_hit': bonus_hit
            }
            results.append(result)
            
            # Print result
            status = "🎉 JACKPOT!" if match_count == 5 and bonus_hit else \
                     "🔥 AMAZING!" if match_count >= 4 else \
                     "✨ GOOD!" if match_count >= 3 else \
                     "👍" if match_count >= 2 else ""
            
            print(f"\n{lottery.upper()} ({target_date}):")
            print(f"  Predicted: {pred['main']} +{pred['bonus']}")
            print(f"  Actual:    {actual_main} +{actual_bonus}")
            print(f"  Result:    {match_count}/5 matches {status}")
            if matches:
                print(f"  Matched:   {sorted(matches)}")
            if bonus_hit:
                print(f"  BONUS HIT! +{actual_bonus}")
    
    # Adjust weights based on performance
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        perf = history['method_performance'].get(lottery, {})
        weights = history.get('learned_weights', {}).get(lottery, {})
        
        if sum(perf.values()) > 0:
            total = sum(perf.values())
            for method in perf:
                method_pct = perf[method] / total if total > 0 else 0.2
                if method_pct > 0.25:
                    weights[method] = min(10, weights.get(method, 5) + 1)
                elif method_pct < 0.15:
                    weights[method] = max(1, weights.get(method, 5) - 1)
            
            if 'learned_weights' not in history:
                history['learned_weights'] = {}
            history['learned_weights'][lottery] = weights
    
    save_history(history)
    return results

def analyze_repeat_patterns():
    """Analyze which numbers from last draw are likely to repeat."""
    print("\n" + "="*70)
    print("REPEAT PATTERN ANALYSIS")
    print("="*70)
    
    findings = {}
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        data_file = DATA_DIR / f'{lottery}.json'
        if not data_file.exists():
            continue
        
        with open(data_file) as f:
            data = json.load(f)
        
        draws = data.get('draws', [])
        if len(draws) < 2:
            continue
        
        # Get numbers from last draw
        last_draw = draws[0]['main']
        
        # Find which of these numbers historically repeat often
        repeat_freq = {}
        for num in last_draw:
            repeat_count = 0
            for i in range(len(draws) - 1):
                if num in draws[i]['main'] and num in draws[i+1]['main']:
                    repeat_count += 1
            repeat_freq[num] = repeat_count
        
        # Sort by repeat frequency
        sorted_nums = sorted(repeat_freq.items(), key=lambda x: -x[1])
        likely_repeats = [n for n, c in sorted_nums if c >= 3][:2]
        
        findings[lottery] = {
            'last_draw': last_draw,
            'repeat_likelihood': sorted_nums,
            'likely_to_repeat': likely_repeats
        }
        
        print(f"\n{lottery.upper()}:")
        print(f"  Last draw: {last_draw}")
        print(f"  Repeat likelihood: {[(n, f'{c} times') for n, c in sorted_nums]}")
        if likely_repeats:
            print(f"  Most likely to repeat: {likely_repeats}")
    
    return findings

def generate_morning_report():
    """Generate comprehensive morning report."""
    print("\n" + "="*70)
    print(f"MORNING EVALUATION REPORT - {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
    print("="*70)
    
    findings = load_findings()
    
    # Check predictions
    results = evaluate_predictions()
    
    # Analyze repeat patterns
    repeat_analysis = analyze_repeat_patterns()
    
    # Get performance summary
    perf = get_performance_summary()
    
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        p = perf.get(lottery, {})
        if p.get('total_predictions', 0) > 0:
            print(f"\n{lottery.upper()}:")
            print(f"  Total predictions: {p['total_predictions']}")
            print(f"  Hit rates: {p.get('hit_rates', {})}")
            print(f"  Avg matches: {p.get('avg_matches', 0):.2f}/5")
            print(f"  3+ rate: {p.get('3_plus_rate', '0%')}")
            print(f"  Learned weights: {p.get('learned_weights', {})}")
    
    # Store daily log
    daily_log = {
        'date': datetime.now().isoformat(),
        'predictions_checked': len(results),
        'results': results,
        'repeat_analysis': {k: {'likely_to_repeat': v['likely_to_repeat']} 
                          for k, v in repeat_analysis.items()},
        'performance': {k: {'total': v.get('total_predictions', 0), 
                           'avg_matches': v.get('avg_matches', 0)}
                       for k, v in perf.items() if isinstance(v, dict)}
    }
    
    findings['daily_logs'].append(daily_log)
    findings['last_evaluation'] = datetime.now().isoformat()
    
    # Store repeat pattern insights
    findings['patterns']['repeat_analysis'] = {
        'l4l_repeat_rate': 45.1,
        'la_repeat_rate': 42.3,
        'common_repeaters': [8, 9],
        'l4l_top_repeaters': [8, 9, 17, 7, 30, 46, 20, 12],
        'la_top_repeaters': [8, 51, 9, 35, 42, 1, 5, 47],
        'insight': 'Nearly half of draws contain at least 1 number from previous draw'
    }
    
    save_findings(findings)
    
    print("\n" + "="*70)
    print("FINDINGS SAVED TO: lottery-tracker/data/permanent_findings.json")
    print("="*70)
    
    return findings

if __name__ == '__main__':
    generate_morning_report()
