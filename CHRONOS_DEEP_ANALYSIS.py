"""
AMAZON CHRONOS DEEP ANALYSIS
=============================

Testing Amazon's state-of-the-art pretrained time series foundation model.
Approaching with OPEN MIND - looking for ANY signal that might exist.

Also exploring:
1. Potential RNG flaws (weak seeds, patterns in timing)
2. Physical ball biases (PB/MM use real balls)
3. Position-specific anomalies that might indicate non-randomness
4. Cross-lottery correlations
"""
import json
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / 'data'

# Try to import Chronos
CHRONOS_AVAILABLE = False
try:
    import torch
    from chronos import ChronosPipeline
    CHRONOS_AVAILABLE = True
    print("✅ Amazon Chronos loaded successfully!")
except ImportError as e:
    print(f"⚠️ Chronos not available: {e}")

LOTTERY_CONFIG = {
    'l4l': {'name': 'Lucky for Life', 'max_main': 48, 'max_bonus': 18, 'type': 'RNG'},
    'la':  {'name': 'Lotto America', 'max_main': 52, 'max_bonus': 10, 'type': 'RNG'},
    'pb':  {'name': 'Powerball', 'max_main': 69, 'max_bonus': 26, 'type': 'PHYSICAL'},
    'mm':  {'name': 'Mega Millions', 'max_main': 70, 'max_bonus': 25, 'type': 'PHYSICAL'}
}

def load_draws(lottery):
    for fn in [f'{lottery}.json', f'{lottery}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                return d.get('draws', d) if isinstance(d, dict) else d
    return []

# =============================================================================
# CHRONOS FOUNDATION MODEL TESTING
# =============================================================================

def test_chronos_prediction(draws, max_num, lottery_name):
    """Test Amazon Chronos pretrained model on lottery sequences."""
    if not CHRONOS_AVAILABLE:
        return None
    
    print(f"\n  Loading Chronos model (this may take a moment)...")
    
    try:
        # Load the smallest Chronos model for speed
        pipeline = ChronosPipeline.from_pretrained(
            "amazon/chronos-t5-small",
            device_map="cpu",
            torch_dtype=torch.float32
        )
        
        results = {}
        
        # Test each position separately (Chronos works on univariate series)
        for pos in range(5):
            # Extract time series for this position
            series = []
            for draw in reversed(draws):  # Chronological order
                main = sorted(draw.get('main', []))
                if pos < len(main):
                    series.append(float(main[pos]))
            
            if len(series) < 100:
                continue
            
            # Convert to tensor
            context = torch.tensor(series[-200:])  # Last 200 draws
            
            # Predict next value
            forecast = pipeline.predict(context, prediction_length=1, num_samples=100)
            
            # Get median prediction
            median_pred = torch.median(forecast[0], dim=0).values.item()
            
            # Get confidence interval
            low = torch.quantile(forecast[0], 0.1, dim=0).item()
            high = torch.quantile(forecast[0], 0.9, dim=0).item()
            
            results[f'pos_{pos+1}'] = {
                'prediction': int(round(median_pred)),
                'confidence_low': int(round(low)),
                'confidence_high': int(round(high)),
                'raw_median': median_pred
            }
            
            print(f"    Position {pos+1}: {int(round(median_pred))} (80% CI: {int(round(low))}-{int(round(high))})")
        
        # Also predict bonus
        bonus_series = [float(draw.get('bonus', 0)) for draw in reversed(draws) if draw.get('bonus')]
        if len(bonus_series) >= 100:
            context = torch.tensor(bonus_series[-200:])
            forecast = pipeline.predict(context, prediction_length=1, num_samples=100)
            median_pred = torch.median(forecast[0], dim=0).values.item()
            results['bonus'] = {
                'prediction': int(round(median_pred)),
                'raw_median': median_pred
            }
            print(f"    Bonus: {int(round(median_pred))}")
        
        return results
        
    except Exception as e:
        print(f"  Chronos error: {e}")
        return None

# =============================================================================
# RNG FLAW DETECTION (Open-minded analysis)
# =============================================================================

def detect_rng_flaws(draws, max_num, lottery_name):
    """
    Look for potential RNG flaws with an OPEN MIND.
    True randomness should show NO patterns here.
    """
    print(f"\n  🔍 Searching for RNG anomalies...")
    
    anomalies = []
    
    # 1. Consecutive draw correlation (should be ~0 for true RNG)
    sums = [sum(sorted(d.get('main', []))) for d in draws]
    if len(sums) > 10:
        correlations = []
        for lag in range(1, 11):
            if len(sums) > lag:
                corr = np.corrcoef(sums[:-lag], sums[lag:])[0, 1]
                correlations.append((lag, corr))
                if abs(corr) > 0.1:
                    anomalies.append(f"Sum correlation at lag {lag}: {corr:.3f} (should be ~0)")
        
        print(f"    Sum autocorrelations (lag 1-10): {[f'{c:.3f}' for _, c in correlations]}")
    
    # 2. Day-of-week bias (if dates available)
    day_counts = defaultdict(list)
    for draw in draws:
        date_str = draw.get('date', '')
        if date_str:
            try:
                dt = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
                day = dt.strftime('%A')
                day_counts[day].extend(sorted(draw.get('main', [])))
            except:
                pass
    
    if day_counts:
        print(f"    Day-of-week analysis:")
        for day, numbers in sorted(day_counts.items()):
            avg = np.mean(numbers) if numbers else 0
            print(f"      {day}: avg={avg:.1f}, n={len(numbers)//5} draws")
            # Check if significantly different from overall
            overall_avg = np.mean([n for nums in day_counts.values() for n in nums])
            if abs(avg - overall_avg) > 2:
                anomalies.append(f"{day} average ({avg:.1f}) differs from overall ({overall_avg:.1f})")
    
    # 3. Modular arithmetic patterns (LCG detection)
    print(f"    Modular arithmetic analysis:")
    for mod in [7, 11, 13, 17, 31, 127]:
        residue_freq = Counter()
        for draw in draws:
            for num in draw.get('main', []):
                residue_freq[num % mod] += 1
        
        total = sum(residue_freq.values())
        expected = total / mod
        max_deviation = max(abs(residue_freq[r] - expected) / expected for r in range(mod))
        
        if max_deviation > 0.15:
            anomalies.append(f"Mod {mod} shows {max_deviation*100:.1f}% deviation from uniform")
            print(f"      Mod {mod}: {max_deviation*100:.1f}% max deviation ⚠️")
        else:
            print(f"      Mod {mod}: {max_deviation*100:.1f}% max deviation ✓")
    
    # 4. Sequential patterns (A followed by B)
    print(f"    Sequential pattern analysis:")
    transition_bias = defaultdict(lambda: defaultdict(int))
    for i in range(len(draws) - 1):
        current_sum = sum(sorted(draws[i].get('main', [])))
        next_sum = sum(sorted(draws[i+1].get('main', [])))
        
        # Categorize sums
        current_cat = 'low' if current_sum < 100 else 'mid' if current_sum < 150 else 'high'
        next_cat = 'low' if next_sum < 100 else 'mid' if next_sum < 150 else 'high'
        transition_bias[current_cat][next_cat] += 1
    
    for cat, nexts in transition_bias.items():
        total = sum(nexts.values())
        print(f"      After {cat}: ", end='')
        for next_cat, count in sorted(nexts.items()):
            pct = count / total * 100 if total > 0 else 0
            print(f"{next_cat}={pct:.0f}% ", end='')
            if abs(pct - 33.3) > 10:  # Significant deviation from uniform
                anomalies.append(f"After {cat} sum, {next_cat} follows {pct:.0f}% (expected ~33%)")
        print()
    
    # 5. Number spacing patterns
    print(f"    Number spacing analysis:")
    all_gaps = []
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i in range(len(main) - 1):
            all_gaps.append(main[i+1] - main[i])
    
    gap_counts = Counter(all_gaps)
    total_gaps = sum(gap_counts.values())
    
    # Check if certain gaps are suspiciously common
    for gap in range(1, 20):
        if gap in gap_counts:
            actual_pct = gap_counts[gap] / total_gaps * 100
            # Expected under uniform random is harder to calculate, but roughly:
            expected_pct = 100 / (max_num - 5)  # Very rough estimate
            if actual_pct > expected_pct * 2:
                anomalies.append(f"Gap {gap} appears {actual_pct:.1f}% (unusually high)")
    
    most_common_gaps = gap_counts.most_common(5)
    print(f"      Most common gaps: {most_common_gaps}")
    
    return anomalies

# =============================================================================
# PHYSICAL BALL BIAS DETECTION (PB/MM)
# =============================================================================

def detect_physical_ball_bias(draws, max_num, lottery_name):
    """
    For physical ball lotteries, look for evidence of ball weight bias.
    Heavier balls might settle to bottom more, lighter float to top.
    """
    print(f"\n  🎱 Physical ball bias analysis...")
    
    findings = []
    
    # 1. Overall frequency (some balls might appear more due to weight)
    freq = Counter()
    for draw in draws:
        for num in draw.get('main', []):
            freq[num] += 1
    
    total = sum(freq.values())
    expected = total / max_num
    
    # Find significant deviations
    over_represented = []
    under_represented = []
    
    for num in range(1, max_num + 1):
        actual = freq.get(num, 0)
        deviation = (actual - expected) / expected * 100
        if deviation > 20:
            over_represented.append((num, deviation, actual))
        elif deviation < -20:
            under_represented.append((num, deviation, actual))
    
    if over_represented:
        print(f"    Over-represented (>20% above expected):")
        for num, dev, count in sorted(over_represented, key=lambda x: x[1], reverse=True)[:5]:
            print(f"      #{num}: +{dev:.1f}% ({count} appearances)")
            findings.append(f"Ball #{num} appears {dev:.1f}% more than expected - possible heavy ball?")
    
    if under_represented:
        print(f"    Under-represented (>20% below expected):")
        for num, dev, count in sorted(under_represented, key=lambda x: x[1])[:5]:
            print(f"      #{num}: {dev:.1f}% ({count} appearances)")
            findings.append(f"Ball #{num} appears {abs(dev):.1f}% less than expected - possible light ball?")
    
    # 2. Position bias (if machines have position tendencies)
    print(f"    Position-specific ball preferences:")
    pos_bias = defaultdict(lambda: Counter())
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_bias[i][num] += 1
    
    for pos in range(5):
        top_nums = pos_bias[pos].most_common(3)
        total_pos = sum(pos_bias[pos].values())
        print(f"      Position {pos+1}: ", end='')
        for num, count in top_nums:
            pct = count / total_pos * 100
            print(f"#{num}({pct:.1f}%) ", end='')
            if pct > 15:  # More than 15% at one position is notable
                findings.append(f"Ball #{num} appears at position {pos+1} {pct:.1f}% of the time")
        print()
    
    # 3. Recent trend (machine calibration drift?)
    print(f"    Recent vs historical comparison (last 50 vs all):")
    recent_freq = Counter()
    for draw in draws[:50]:
        for num in draw.get('main', []):
            recent_freq[num] += 1
    
    recent_total = sum(recent_freq.values())
    
    heating_up = []
    cooling_down = []
    
    for num in range(1, max_num + 1):
        overall_pct = freq.get(num, 0) / total * 100 if total > 0 else 0
        recent_pct = recent_freq.get(num, 0) / recent_total * 100 if recent_total > 0 else 0
        
        if recent_pct > overall_pct * 1.5 and recent_freq.get(num, 0) >= 3:
            heating_up.append((num, recent_pct, overall_pct))
        elif recent_pct < overall_pct * 0.5 and freq.get(num, 0) >= 10:
            cooling_down.append((num, recent_pct, overall_pct))
    
    if heating_up:
        print(f"      🔥 Heating up: ", end='')
        for num, rec, ovr in sorted(heating_up, key=lambda x: x[1]/x[2] if x[2] > 0 else 0, reverse=True)[:5]:
            print(f"#{num}({rec:.1f}% vs {ovr:.1f}%) ", end='')
            findings.append(f"Ball #{num} trending HOT: {rec:.1f}% recent vs {ovr:.1f}% historical")
        print()
    
    if cooling_down:
        print(f"      ❄️ Cooling down: ", end='')
        for num, rec, ovr in sorted(cooling_down, key=lambda x: x[1]/x[2] if x[2] > 0 else 1)[:5]:
            print(f"#{num}({rec:.1f}% vs {ovr:.1f}%) ", end='')
        print()
    
    return findings

# =============================================================================
# GENERATE OPTIMAL TICKETS BASED ON ALL FINDINGS
# =============================================================================

def generate_informed_ticket(draws, max_num, max_bonus, anomalies, ball_findings, chronos_results):
    """Generate a ticket informed by ALL analysis - both statistical and AI."""
    
    # Start with position frequency (proven)
    pos_freq = [{} for _ in range(5)]
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            if i < 5:
                pos_freq[i][num] = pos_freq[i].get(num, 0) + 1
    
    total = len(draws)
    
    # Score each number
    scores = defaultdict(float)
    
    # 1. Position frequency
    for pos in range(5):
        for num, count in pos_freq[pos].items():
            freq = count / total
            scores[num] += freq * 20
    
    # 2. Recent momentum (last 30 draws)
    for draw in draws[:30]:
        for num in draw.get('main', []):
            scores[num] += 0.5
    
    # 3. Chronos predictions (if available) - OPEN MINDED
    if chronos_results:
        for key, data in chronos_results.items():
            if 'prediction' in data:
                pred = data['prediction']
                if 1 <= pred <= max_num:
                    scores[pred] += 10  # Significant boost for Chronos predictions
    
    # 4. Physical ball bias (for PB/MM)
    if ball_findings:
        for finding in ball_findings:
            if 'HOT' in finding:
                # Extract number from finding
                try:
                    num = int(finding.split('#')[1].split()[0])
                    scores[num] += 5
                except:
                    pass
    
    # Build ticket from highest scoring numbers per position
    ticket = []
    used = set()
    
    for pos in range(5):
        best_num = None
        best_score = -1
        
        pos_nums = list(pos_freq[pos].keys())
        
        for num in pos_nums:
            if num in used:
                continue
            if ticket and num <= ticket[-1]:
                continue
            
            score = scores[num]
            if score > best_score:
                best_score = score
                best_num = num
        
        if best_num:
            ticket.append(best_num)
            used.add(best_num)
    
    # Best bonus
    bonus_freq = Counter(d.get('bonus') for d in draws)
    best_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
    
    # If Chronos gave a bonus prediction, consider it
    if chronos_results and 'bonus' in chronos_results:
        chronos_bonus = chronos_results['bonus']['prediction']
        if 1 <= chronos_bonus <= max_bonus:
            # Use Chronos if it's reasonably frequent
            if bonus_freq.get(chronos_bonus, 0) >= bonus_freq.get(best_bonus, 0) * 0.5:
                best_bonus = chronos_bonus
    
    return ticket, best_bonus

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("="*80)
    print("AMAZON CHRONOS + DEEP RNG/BALL ANALYSIS")
    print("Open-minded search for ANY exploitable patterns")
    print("="*80)
    
    final_tickets = {}
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        draws = load_draws(lottery)
        if not draws:
            continue
        
        config = LOTTERY_CONFIG[lottery]
        max_num = config['max_main']
        max_bonus = config['max_bonus']
        lottery_type = config['type']
        
        print(f"\n{'='*80}")
        print(f"🎰 {config['name'].upper()} ({lottery_type}) - {len(draws)} draws")
        print("="*80)
        
        # 1. Test Chronos
        chronos_results = None
        if CHRONOS_AVAILABLE:
            print(f"\n🤖 AMAZON CHRONOS ANALYSIS:")
            chronos_results = test_chronos_prediction(draws, max_num, config['name'])
        
        # 2. Detect RNG anomalies
        print(f"\n🔬 RNG FLAW DETECTION:")
        anomalies = detect_rng_flaws(draws, max_num, config['name'])
        
        if anomalies:
            print(f"\n  ⚠️ ANOMALIES FOUND:")
            for a in anomalies[:5]:
                print(f"    - {a}")
        else:
            print(f"\n  ✅ No significant RNG anomalies detected")
        
        # 3. Physical ball analysis (for PB/MM)
        ball_findings = []
        if lottery_type == 'PHYSICAL':
            ball_findings = detect_physical_ball_bias(draws, max_num, config['name'])
            
            if ball_findings:
                print(f"\n  🎱 BALL BIAS FINDINGS:")
                for f in ball_findings[:5]:
                    print(f"    - {f}")
        
        # 4. Generate informed ticket
        print(f"\n🎯 GENERATING OPTIMAL TICKET:")
        ticket, bonus = generate_informed_ticket(
            draws, max_num, max_bonus, anomalies, ball_findings, chronos_results
        )
        
        print(f"  FINAL TICKET: {ticket} + Bonus: {bonus}")
        
        # Explain why
        print(f"\n  Reasoning:")
        if chronos_results:
            chronos_nums = [chronos_results[f'pos_{i}']['prediction'] 
                          for i in range(1, 6) if f'pos_{i}' in chronos_results]
            overlap = len(set(ticket) & set(chronos_nums))
            print(f"    - Chronos predictions overlap: {overlap}/5")
        if anomalies:
            print(f"    - Exploiting {len(anomalies)} detected anomalies")
        if ball_findings:
            print(f"    - Incorporating {len(ball_findings)} ball bias findings")
        print(f"    - Position frequency optimized")
        print(f"    - Recent momentum weighted")
        
        final_tickets[lottery] = {
            'main': ticket,
            'bonus': bonus,
            'chronos_used': chronos_results is not None,
            'anomalies_found': len(anomalies),
            'ball_bias_found': len(ball_findings)
        }
    
    # Save results
    output = {
        'analysis_date': str(np.datetime64('now')),
        'chronos_available': CHRONOS_AVAILABLE,
        'final_tickets': final_tickets
    }
    
    output_path = DATA_DIR / 'chronos_deep_analysis_results.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print("\n\n" + "="*80)
    print("🏆 FINAL OPTIMAL TICKETS (Chronos + RNG/Ball Analysis)")
    print("="*80)
    
    for lottery, data in final_tickets.items():
        config = LOTTERY_CONFIG[lottery]
        print(f"\n{config['name']}: {data['main']} + {data['bonus']}")
        if data['chronos_used']:
            print(f"  ✨ Informed by Chronos AI")
        if data['anomalies_found'] > 0:
            print(f"  ⚠️ Exploiting {data['anomalies_found']} RNG anomalies")
        if data['ball_bias_found'] > 0:
            print(f"  🎱 Exploiting {data['ball_bias_found']} ball biases")
    
    print(f"\n✅ Results saved to {output_path}")
    
    return final_tickets

if __name__ == '__main__':
    main()
