"""
Check if any HOLD tickets have ever hit 5/5 or jackpot historically.
"""
import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / 'data'

# Current HOLD tickets (Jan 22, 2026 - Chronos + Ball Bias)
CURRENT_HOLD_TICKETS = {
    'l4l': {'main': [3, 12, 17, 38, 46], 'bonus': 11, 'name': 'Lucky for Life'},
    'la': {'main': [4, 15, 25, 42, 51], 'bonus': 4, 'name': 'Lotto America'},
    'pb': {'main': [28, 33, 53, 64, 69], 'bonus': 20, 'name': 'Powerball'},
    'mm': {'main': [10, 18, 27, 42, 68], 'bonus': 1, 'name': 'Mega Millions'}
}

# Previous HOLD tickets to also check
PREVIOUS_HOLD_TICKETS = {
    'l4l_v1': {'main': [1, 12, 30, 39, 47], 'bonus': 11, 'name': 'Lucky for Life (v1)'},
    'la_v1': {'main': [1, 15, 23, 42, 51], 'bonus': 4, 'name': 'Lotto America (v1)'},
    'pb_v1': {'main': [1, 11, 33, 52, 69], 'bonus': 20, 'name': 'Powerball (v1)'},
    'mm_v1': {'main': [6, 10, 27, 42, 68], 'bonus': 24, 'name': 'Mega Millions (v1)'},
    'pb_v2': {'main': [4, 21, 35, 61, 69], 'bonus': 21, 'name': 'Powerball (v2)'},
    'mm_v2': {'main': [18, 21, 27, 42, 68], 'bonus': 24, 'name': 'Mega Millions (v2)'},
}

def load_draws(lottery):
    """Load historical draws for a lottery."""
    lottery_key = lottery.split('_')[0]  # Handle versioned keys
    for fn in [f'{lottery_key}.json', f'{lottery_key}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                return d.get('draws', d) if isinstance(d, dict) else d
    return []

def check_ticket_wins(ticket_main, ticket_bonus, draws, ticket_name):
    """Check how many times a ticket matched 3/5, 4/5, 5/5, or jackpot."""
    results = {
        '3_of_5': [],
        '4_of_5': [],
        '5_of_5': [],
        'jackpot': []
    }
    
    ticket_set = set(ticket_main)
    
    for draw in draws:
        draw_main = set(draw.get('main', []))
        draw_bonus = draw.get('bonus')
        draw_date = draw.get('date', 'Unknown')
        
        matches = len(ticket_set & draw_main)
        bonus_match = ticket_bonus == draw_bonus
        
        if matches == 5:
            if bonus_match:
                results['jackpot'].append({
                    'date': draw_date,
                    'draw_main': sorted(draw_main),
                    'draw_bonus': draw_bonus,
                    'ticket': ticket_main,
                    'ticket_bonus': ticket_bonus
                })
            else:
                results['5_of_5'].append({
                    'date': draw_date,
                    'draw_main': sorted(draw_main),
                    'draw_bonus': draw_bonus,
                    'ticket': ticket_main,
                    'ticket_bonus': ticket_bonus
                })
        elif matches == 4:
            results['4_of_5'].append({
                'date': draw_date,
                'matches': matches,
                'bonus_match': bonus_match
            })
        elif matches == 3:
            results['3_of_5'].append({
                'date': draw_date,
                'matches': matches,
                'bonus_match': bonus_match
            })
    
    return results

def main():
    print("="*80)
    print("HOLD TICKET HISTORICAL WIN CHECK")
    print("Checking if any HOLD tickets ever hit 5/5 or jackpot")
    print("="*80)
    
    all_results = {}
    
    # Check current tickets
    print("\n📌 CURRENT HOLD TICKETS (Jan 22, 2026)")
    print("-"*60)
    
    for lottery, ticket in CURRENT_HOLD_TICKETS.items():
        draws = load_draws(lottery)
        if not draws:
            print(f"  {ticket['name']}: No data available")
            continue
        
        results = check_ticket_wins(ticket['main'], ticket['bonus'], draws, ticket['name'])
        all_results[f"current_{lottery}"] = results
        
        print(f"\n🎰 {ticket['name']}")
        print(f"   Ticket: {ticket['main']} + {ticket['bonus']}")
        print(f"   Historical draws checked: {len(draws)}")
        print(f"   ")
        print(f"   🏆 JACKPOTS (5/5 + bonus): {len(results['jackpot'])}")
        print(f"   ⭐ 5/5 (no bonus): {len(results['5_of_5'])}")
        print(f"   🎯 4/5: {len(results['4_of_5'])}")
        print(f"   ✓ 3/5: {len(results['3_of_5'])}")
        
        if results['jackpot']:
            print(f"\n   💰 JACKPOT MATCHES:")
            for win in results['jackpot']:
                print(f"      Date: {win['date']}")
                print(f"      Draw: {win['draw_main']} + {win['draw_bonus']}")
        
        if results['5_of_5']:
            print(f"\n   ⭐ 5/5 MATCHES (no bonus):")
            for win in results['5_of_5']:
                print(f"      Date: {win['date']}")
                print(f"      Draw: {win['draw_main']} + {win['draw_bonus']}")
    
    # Check previous tickets
    print("\n\n📜 PREVIOUS HOLD TICKETS (Historical versions)")
    print("-"*60)
    
    for lottery, ticket in PREVIOUS_HOLD_TICKETS.items():
        draws = load_draws(lottery)
        if not draws:
            continue
        
        results = check_ticket_wins(ticket['main'], ticket['bonus'], draws, ticket['name'])
        all_results[f"prev_{lottery}"] = results
        
        print(f"\n🎰 {ticket['name']}")
        print(f"   Ticket: {ticket['main']} + {ticket['bonus']}")
        print(f"   🏆 Jackpots: {len(results['jackpot'])} | ⭐ 5/5: {len(results['5_of_5'])} | 🎯 4/5: {len(results['4_of_5'])} | ✓ 3/5: {len(results['3_of_5'])}")
        
        if results['jackpot']:
            print(f"   💰 JACKPOT MATCHES:")
            for win in results['jackpot']:
                print(f"      {win['date']}: {win['draw_main']} + {win['draw_bonus']}")
        
        if results['5_of_5']:
            print(f"   ⭐ 5/5 MATCHES:")
            for win in results['5_of_5']:
                print(f"      {win['date']}: {win['draw_main']} + {win['draw_bonus']}")
    
    # Summary
    print("\n\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    total_jackpots = sum(len(r['jackpot']) for r in all_results.values())
    total_5of5 = sum(len(r['5_of_5']) for r in all_results.values())
    total_4of5 = sum(len(r['4_of_5']) for r in all_results.values())
    total_3of5 = sum(len(r['3_of_5']) for r in all_results.values())
    
    print(f"\n  Total JACKPOTS across all tickets: {total_jackpots}")
    print(f"  Total 5/5 (no bonus): {total_5of5}")
    print(f"  Total 4/5: {total_4of5}")
    print(f"  Total 3/5: {total_3of5}")
    
    if total_jackpots == 0 and total_5of5 == 0:
        print(f"\n  ⚠️ NO 5/5 OR JACKPOT MATCHES FOUND")
        print(f"  This is EXPECTED - jackpots are extremely rare (1 in 26M - 302M)")
        print(f"  The tickets are optimized for PROBABILITY, not guaranteed wins")
    
    # Save results
    output_path = DATA_DIR / 'hold_ticket_win_history.json'
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to {output_path}")

if __name__ == '__main__':
    main()
