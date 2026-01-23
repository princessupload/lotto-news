"""
Analyze 5/5 and jackpot repeat patterns across all lotteries.
Build exclusion lists of combinations that should NEVER be played again.

Key insight: If no jackpot/5-of-5 has EVER repeated, we can exclude all past winners!
"""
import json
from pathlib import Path
from itertools import combinations
from collections import Counter

DATA_DIR = Path(__file__).parent / 'data'

def load_draws(lottery):
    """Load all draws for a lottery."""
    path = DATA_DIR / f'{lottery}.json'
    if path.exists():
        with open(path) as f:
            data = json.load(f)
            return data.get('draws', [])
    return []

def analyze_exact_repeats(draws):
    """Check if any exact 5/5 combination has repeated."""
    seen = {}
    repeats = []
    
    for i, draw in enumerate(draws):
        main = tuple(sorted(draw['main']))
        if main in seen:
            repeats.append({
                'combo': list(main),
                'first_date': seen[main]['date'],
                'repeat_date': draw['date'],
                'gap': i - seen[main]['index']
            })
        else:
            seen[main] = {'date': draw['date'], 'index': i}
    
    return repeats, len(seen)

def analyze_jackpot_repeats(draws):
    """Check if any exact 6/6 (5/5 + bonus) has repeated."""
    seen = {}
    repeats = []
    
    for i, draw in enumerate(draws):
        main = tuple(sorted(draw['main']))
        bonus = draw['bonus']
        jackpot = (main, bonus)
        
        if jackpot in seen:
            repeats.append({
                'combo': list(main) + [bonus],
                'first_date': seen[jackpot]['date'],
                'repeat_date': draw['date']
            })
        else:
            seen[jackpot] = {'date': draw['date'], 'index': i}
    
    return repeats, len(seen)

def analyze_partial_repeats(draws, match_count=4):
    """Analyze how often 4/5 or 3/5 combinations repeat."""
    combo_counts = Counter()
    
    for draw in draws:
        main = sorted(draw['main'])
        for combo in combinations(main, match_count):
            combo_counts[combo] += 1
    
    repeating = {k: v for k, v in combo_counts.items() if v > 1}
    return repeating, len(combo_counts)

def build_exclusion_set(draws):
    """Build set of all past 5/5 combinations to exclude from future picks."""
    exclusions = set()
    for draw in draws:
        main = tuple(sorted(draw['main']))
        exclusions.add(main)
    return exclusions

def main():
    results = {}
    all_exclusions = {}
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        draws = load_draws(lottery)
        if not draws:
            print(f"\n{lottery.upper()}: No data")
            continue
        
        print(f"\n{'='*60}")
        print(f"{lottery.upper()} ANALYSIS ({len(draws)} draws)")
        print('='*60)
        
        # Exact 5/5 repeats
        repeats_5, unique_5 = analyze_exact_repeats(draws)
        print(f"\n5/5 EXACT REPEATS: {len(repeats_5)}")
        print(f"Unique 5/5 combos: {unique_5}")
        if repeats_5:
            print("REPEATS FOUND:")
            for r in repeats_5:
                print(f"  {r['combo']} - First: {r['first_date']}, Repeat: {r['repeat_date']}")
        else:
            print("✅ NO 5/5 REPEATS - All past combos can be excluded!")
        
        # Jackpot (6/6) repeats
        repeats_6, unique_6 = analyze_jackpot_repeats(draws)
        print(f"\n6/6 JACKPOT REPEATS: {len(repeats_6)}")
        print(f"Unique jackpots: {unique_6}")
        if repeats_6:
            for r in repeats_6:
                print(f"  {r['combo']} - First: {r['first_date']}, Repeat: {r['repeat_date']}")
        else:
            print("✅ NO JACKPOT REPEATS - Safe to exclude all past jackpots!")
        
        # 4/5 partial repeats
        repeats_4, unique_4 = analyze_partial_repeats(draws, 4)
        max_4 = max(repeats_4.values()) if repeats_4 else 0
        top_4 = sorted(repeats_4.items(), key=lambda x: -x[1])[:5]
        print(f"\n4/5 REPEATING COMBOS: {len(repeats_4)} (max appearances: {max_4})")
        if top_4:
            print("Top 4/5 combos:")
            for combo, count in top_4:
                print(f"  {list(combo)}: {count}x")
        
        # 3/5 partial repeats
        repeats_3, unique_3 = analyze_partial_repeats(draws, 3)
        max_3 = max(repeats_3.values()) if repeats_3 else 0
        top_3 = sorted(repeats_3.items(), key=lambda x: -x[1])[:5]
        print(f"\n3/5 REPEATING COMBOS: {len(repeats_3)} (max appearances: {max_3})")
        if top_3:
            print("Top 3/5 combos:")
            for combo, count in top_3:
                print(f"  {list(combo)}: {count}x")
        
        # Build exclusion set
        exclusions = build_exclusion_set(draws)
        all_exclusions[lottery] = [list(e) for e in exclusions]
        
        results[lottery] = {
            'draws': len(draws),
            'unique_5of5': unique_5,
            'repeats_5of5': len(repeats_5),
            'unique_jackpots': unique_6,
            'repeats_jackpots': len(repeats_6),
            'repeating_4of5': len(repeats_4),
            'max_4of5_repeats': max_4,
            'repeating_3of5': len(repeats_3),
            'max_3of5_repeats': max_3,
            'exclusion_count': len(exclusions)
        }
    
    # Save exclusion lists
    exclusions_path = DATA_DIR / 'past_winners_exclusions.json'
    with open(exclusions_path, 'w') as f:
        json.dump(all_exclusions, f, indent=2)
    print(f"\n✅ Saved exclusion lists to {exclusions_path}")
    
    # Save analysis results
    results_path = DATA_DIR / 'repeat_analysis.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Saved analysis to {results_path}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY: CAN WE EXCLUDE PAST WINNERS?")
    print("="*60)
    for lottery, r in results.items():
        status = "✅ YES" if r['repeats_5of5'] == 0 else "❌ NO (repeats exist)"
        print(f"{lottery.upper()}: {status} - {r['exclusion_count']} combos to exclude")
    
    total_exclusions = sum(len(v) for v in all_exclusions.values())
    print(f"\nTOTAL EXCLUSIONS ACROSS ALL LOTTERIES: {total_exclusions}")
    
    return results, all_exclusions

if __name__ == '__main__':
    main()
