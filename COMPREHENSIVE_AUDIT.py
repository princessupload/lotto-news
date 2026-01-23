"""
COMPREHENSIVE AUDIT: Check HOLD tickets vs pools, verify all methods are consistent.
"""
import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent / 'data'

# CORRECTED HOLD tickets - Combined Method Optimal (Jan 23, 2026)
# Pos Freq + Pair Freq + Momentum - Backtested for best 2+/5 rates
CURRENT_HOLD = {
    'l4l': {'main': [1, 12, 30, 39, 46], 'bonus': 11},
    'la': {'main': [1, 15, 23, 42, 51], 'bonus': 1},
    'pb': {'main': [1, 11, 27, 53, 68], 'bonus': 20},
    'mm': {'main': [2, 18, 27, 42, 59], 'bonus': 1}
}

LOTTERY_CONFIG = {
    'l4l': {'name': 'Lucky for Life', 'max_main': 48, 'max_bonus': 18, 'main_count': 5},
    'la': {'name': 'Lotto America', 'max_main': 52, 'max_bonus': 10, 'main_count': 5},
    'pb': {'name': 'Powerball', 'max_main': 69, 'max_bonus': 26, 'main_count': 5},
    'mm': {'name': 'Mega Millions', 'max_main': 70, 'max_bonus': 25, 'main_count': 5}
}

def load_draws(lottery):
    """Load historical draws."""
    for fn in [f'{lottery}.json', f'{lottery}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                return d.get('draws', d) if isinstance(d, dict) else d
    return []

def generate_position_pools(draws, main_count=5, top_n=8):
    """Generate position frequency pools - THE VALIDATED METHOD."""
    position_counters = [Counter() for _ in range(main_count)]
    
    for draw in draws:
        main_nums = sorted(draw.get('main', []))
        for i, num in enumerate(main_nums):
            if i < main_count:
                position_counters[i][num] += 1
    
    pools = []
    for counter in position_counters:
        top_nums = [num for num, _ in counter.most_common(top_n)]
        pools.append(sorted(top_nums))
    
    return pools, position_counters

def generate_bonus_pool(draws, top_n=5):
    """Generate bonus frequency pool."""
    bonus_counter = Counter()
    for draw in draws:
        bonus = draw.get('bonus')
        if bonus:
            bonus_counter[bonus] += 1
    return sorted([num for num, _ in bonus_counter.most_common(top_n)]), bonus_counter

def find_optimal_ticket_from_pools(pools, position_counters):
    """Find the optimal ticket by selecting highest frequency number per position."""
    ticket = []
    used = set()
    
    for pos, counter in enumerate(position_counters):
        # Get numbers sorted by frequency for this position
        sorted_nums = [num for num, _ in counter.most_common()]
        
        for num in sorted_nums:
            if num not in used:
                ticket.append(num)
                used.add(num)
                break
    
    return sorted(ticket)

def audit_lottery(lottery):
    """Full audit for one lottery."""
    config = LOTTERY_CONFIG[lottery]
    draws = load_draws(lottery)
    
    if not draws:
        return {'error': f'No data for {lottery}'}
    
    print(f"\n{'='*70}")
    print(f"🔍 AUDIT: {config['name']} ({len(draws)} draws)")
    print('='*70)
    
    # Generate pools using position frequency (THE validated method)
    pools, pos_counters = generate_position_pools(draws, top_n=8)
    bonus_pool, bonus_counter = generate_bonus_pool(draws, top_n=5)
    
    # Current HOLD ticket
    hold = CURRENT_HOLD[lottery]
    hold_main = hold['main']
    hold_bonus = hold['bonus']
    
    print(f"\n📌 Current HOLD Ticket: {hold_main} + {hold_bonus}")
    
    # Check if each HOLD number is in its position pool
    print(f"\n📊 Position Pools (Top 8 per position):")
    issues = []
    for pos, (pool, num) in enumerate(zip(pools, hold_main)):
        in_pool = "✅" if num in pool else "❌ NOT IN POOL"
        freq = pos_counters[pos].get(num, 0)
        total = sum(pos_counters[pos].values())
        pct = (freq / total * 100) if total > 0 else 0
        print(f"   Position {pos+1}: {pool}")
        print(f"      HOLD #{num}: {in_pool} (freq: {freq}/{total} = {pct:.1f}%)")
        
        if num not in pool:
            # Find rank of this number
            rank = list(pos_counters[pos].keys()).index(num) + 1 if num in pos_counters[pos] else 'NOT FOUND'
            issues.append({
                'position': pos + 1,
                'hold_num': num,
                'pool': pool,
                'rank': rank,
                'freq_pct': pct
            })
    
    # Bonus check
    bonus_in_pool = "✅" if hold_bonus in bonus_pool else "❌ NOT IN POOL"
    bonus_freq = bonus_counter.get(hold_bonus, 0)
    bonus_total = sum(bonus_counter.values())
    bonus_pct = (bonus_freq / bonus_total * 100) if bonus_total > 0 else 0
    print(f"\n🎱 Bonus Pool (Top 5): {bonus_pool}")
    print(f"   HOLD Bonus #{hold_bonus}: {bonus_in_pool} (freq: {bonus_freq}/{bonus_total} = {bonus_pct:.1f}%)")
    
    if hold_bonus not in bonus_pool:
        bonus_rank = list(bonus_counter.keys()).index(hold_bonus) + 1 if hold_bonus in bonus_counter else 'NOT FOUND'
        issues.append({
            'position': 'bonus',
            'hold_num': hold_bonus,
            'pool': bonus_pool,
            'rank': bonus_rank,
            'freq_pct': bonus_pct
        })
    
    # Calculate what the OPTIMAL ticket should be (pure position frequency)
    optimal = find_optimal_ticket_from_pools(pools, pos_counters)
    optimal_bonus = bonus_pool[0] if bonus_pool else 1
    
    print(f"\n🏆 OPTIMAL TICKET (Pure Position Frequency):")
    print(f"   Main: {optimal}")
    print(f"   Bonus: {optimal_bonus}")
    
    # Compare HOLD vs OPTIMAL
    match_count = len(set(hold_main) & set(optimal))
    print(f"\n📈 HOLD vs OPTIMAL Comparison:")
    print(f"   Matching numbers: {match_count}/5")
    print(f"   HOLD: {hold_main} + {hold_bonus}")
    print(f"   OPTIMAL: {optimal} + {optimal_bonus}")
    
    if issues:
        print(f"\n⚠️ ISSUES FOUND: {len(issues)}")
        for issue in issues:
            print(f"   - Position {issue['position']}: #{issue['hold_num']} ranked #{issue['rank']} ({issue['freq_pct']:.1f}%), not in top 8")
    
    return {
        'lottery': lottery,
        'draws': len(draws),
        'hold_ticket': hold_main,
        'hold_bonus': hold_bonus,
        'optimal_ticket': optimal,
        'optimal_bonus': optimal_bonus,
        'pools': pools,
        'bonus_pool': bonus_pool,
        'issues': issues,
        'match_count': match_count
    }

def main():
    print("="*70)
    print("COMPREHENSIVE LOTTERY SYSTEM AUDIT")
    print("Checking HOLD tickets vs Position Frequency Pools")
    print("="*70)
    
    all_results = {}
    total_issues = 0
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        result = audit_lottery(lottery)
        all_results[lottery] = result
        if 'issues' in result:
            total_issues += len(result['issues'])
    
    # Summary
    print("\n\n" + "="*70)
    print("📋 AUDIT SUMMARY")
    print("="*70)
    
    print(f"\n⚠️ TOTAL ISSUES: {total_issues}")
    
    if total_issues > 0:
        print("\n🔧 RECOMMENDED FIXES:")
        for lottery, result in all_results.items():
            if result.get('issues'):
                config = LOTTERY_CONFIG[lottery]
                print(f"\n   {config['name']}:")
                print(f"      Current HOLD: {result['hold_ticket']} + {result['hold_bonus']}")
                print(f"      Recommended:  {result['optimal_ticket']} + {result['optimal_bonus']}")
    
    # Save audit results
    output_path = DATA_DIR / 'comprehensive_audit_results.json'
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n✅ Full audit results saved to {output_path}")
    
    return all_results

if __name__ == '__main__':
    main()
