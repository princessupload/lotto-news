"""
CHECK USER'S HOLD TICKETS
==========================
Checks if user's personal HOLD tickets have hit 5/5 or jackpot.
Triggers congratulations banner if they win!
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / 'data'

def load_user_tickets():
    try:
        with open(DATA_DIR / 'user_hold_tickets.json') as f:
            return json.load(f)
    except:
        return None

def save_user_tickets(data):
    with open(DATA_DIR / 'user_hold_tickets.json', 'w') as f:
        json.dump(data, f, indent=2)

def load_lottery_data(lottery):
    try:
        with open(DATA_DIR / f'{lottery}.json') as f:
            return json.load(f)
    except:
        return None

def check_user_tickets():
    """Check user's HOLD tickets against latest draws. Returns win info if any."""
    user_data = load_user_tickets()
    if not user_data:
        return None
    
    results = {
        'checked': datetime.now().isoformat(),
        'wins': [],
        'matches': []
    }
    
    for lottery, ticket_info in user_data.get('tickets', {}).items():
        lottery_data = load_lottery_data(lottery)
        if not lottery_data:
            continue
        
        draws = lottery_data.get('draws', [])
        if not draws:
            continue
        
        latest = draws[0]
        latest_date = latest.get('date')
        latest_main = set(latest.get('main', []))
        latest_bonus = latest.get('bonus')
        
        user_main = set(ticket_info['main'])
        user_bonus = ticket_info['bonus']
        
        # Count matches
        main_matches = len(user_main & latest_main)
        bonus_match = user_bonus == latest_bonus
        
        match_info = {
            'lottery': lottery,
            'name': ticket_info['name'],
            'date': latest_date,
            'user_ticket': ticket_info['main'],
            'user_bonus': user_bonus,
            'drawn': list(latest_main),
            'drawn_bonus': latest_bonus,
            'main_matches': main_matches,
            'bonus_match': bonus_match
        }
        
        results['matches'].append(match_info)
        
        # Check for wins!
        if main_matches == 5:
            if bonus_match:
                # JACKPOT!!!
                win = {
                    'type': 'JACKPOT',
                    'lottery': lottery,
                    'name': ticket_info['name'],
                    'date': latest_date,
                    'ticket': ticket_info['main'],
                    'bonus': user_bonus
                }
                results['wins'].append(win)
                
                # Save to permanent record
                if win not in user_data['wins']['jackpot']:
                    user_data['wins']['jackpot'].append(win)
                    save_user_tickets(user_data)
            else:
                # 5/5 match!
                win = {
                    'type': '5_OF_5',
                    'lottery': lottery,
                    'name': ticket_info['name'],
                    'date': latest_date,
                    'ticket': ticket_info['main'],
                    'bonus': user_bonus,
                    'drawn_bonus': latest_bonus
                }
                results['wins'].append(win)
                
                # Save to permanent record
                if win not in user_data['wins']['5_of_5']:
                    user_data['wins']['5_of_5'].append(win)
                    save_user_tickets(user_data)
    
    # Update check history
    user_data['check_history'].append({
        'date': results['checked'],
        'any_wins': len(results['wins']) > 0
    })
    # Keep only last 100 checks
    user_data['check_history'] = user_data['check_history'][-100:]
    save_user_tickets(user_data)
    
    return results

def get_congratulations_banner():
    """Returns HTML/text banner if user has any wins."""
    user_data = load_user_tickets()
    if not user_data:
        return None
    
    jackpots = user_data.get('wins', {}).get('jackpot', [])
    five_of_five = user_data.get('wins', {}).get('5_of_5', [])
    
    if jackpots:
        win = jackpots[-1]
        return {
            'type': 'JACKPOT',
            'show': True,
            'html': f'''
                <div style="background: linear-gradient(45deg, #FFD700, #FFA500); 
                            padding: 20px; text-align: center; border-radius: 10px;
                            animation: pulse 1s infinite; margin: 20px 0;">
                    <h1 style="color: #000; font-size: 48px; margin: 0;">🎉 JACKPOT WINNER! 🎉</h1>
                    <h2 style="color: #000; margin: 10px 0;">{win['name']}</h2>
                    <p style="color: #000; font-size: 24px;">
                        Your HOLD ticket {win['ticket']} + {win['bonus']} WON on {win['date']}!
                    </p>
                </div>
            ''',
            'text': f"🎉🎉🎉 JACKPOT WINNER! {win['name']} - {win['ticket']} + {win['bonus']} on {win['date']}! 🎉🎉🎉"
        }
    
    if five_of_five:
        win = five_of_five[-1]
        return {
            'type': '5_OF_5',
            'show': True,
            'html': f'''
                <div style="background: linear-gradient(45deg, #4CAF50, #8BC34A); 
                            padding: 20px; text-align: center; border-radius: 10px;
                            margin: 20px 0;">
                    <h1 style="color: #fff; font-size: 36px; margin: 0;">🎊 5/5 MATCH! 🎊</h1>
                    <h2 style="color: #fff; margin: 10px 0;">{win['name']}</h2>
                    <p style="color: #fff; font-size: 20px;">
                        Your HOLD ticket {win['ticket']} matched all 5 main numbers on {win['date']}!
                    </p>
                    <p style="color: #fff;">Bonus needed: {win['bonus']}, Drawn: {win['drawn_bonus']}</p>
                </div>
            ''',
            'text': f"🎊 5/5 MATCH! {win['name']} - {win['ticket']} on {win['date']}! 🎊"
        }
    
    return {'show': False}

def print_status():
    """Print current status of user's tickets."""
    user_data = load_user_tickets()
    if not user_data:
        print("No user tickets found.")
        return
    
    print("="*70)
    print("YOUR HOLD FOREVER TICKETS")
    print("="*70)
    
    for lottery, info in user_data['tickets'].items():
        print(f"\n{info['name']}:")
        print(f"  Main: {info['main']}")
        print(f"  Bonus: {info['bonus']}")
    
    # Check latest results
    results = check_user_tickets()
    
    print("\n" + "="*70)
    print("LATEST DRAW MATCHES")
    print("="*70)
    
    for match in results.get('matches', []):
        emoji = "🎉" if match['main_matches'] >= 3 else ""
        bonus_str = "✓" if match['bonus_match'] else "✗"
        print(f"\n{match['name']} ({match['date']}):")
        print(f"  Your ticket: {match['user_ticket']} + {match['user_bonus']}")
        print(f"  Drawn:       {match['drawn']} + {match['drawn_bonus']}")
        print(f"  Matches:     {match['main_matches']}/5 main, Bonus: {bonus_str} {emoji}")
    
    # Check for wins
    if results.get('wins'):
        print("\n" + "🎉"*35)
        for win in results['wins']:
            print(f"\n  *** {win['type']} WINNER! ***")
            print(f"  {win['name']} on {win['date']}")
        print("\n" + "🎉"*35)
    else:
        jackpots = user_data.get('wins', {}).get('jackpot', [])
        five_of_five = user_data.get('wins', {}).get('5_of_5', [])
        print(f"\nHistorical wins: {len(jackpots)} jackpots, {len(five_of_five)} 5/5 matches")

if __name__ == '__main__':
    print_status()
