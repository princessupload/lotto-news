"""Check what the new optimal tickets would be with pure position frequency."""
import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent / 'data'

def load_draws(lottery):
    for filename in [f'{lottery}_historical_data.json', f'{lottery}.json']:
        path = DATA_DIR / filename
        if path.exists():
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get('draws', [])
                return data
    return []

def calculate_optimal_ticket(lottery, draws):
    if len(draws) < 50:
        return None
    
    pos_freq = {i: Counter() for i in range(5)}
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main):
            pos_freq[i][num] += 1
    
    top_per_pos = []
    for i in range(5):
        top_per_pos.append([num for num, _ in pos_freq[i].most_common(8)])
    
    best_ticket = None
    best_score = -1
    
    for n1 in top_per_pos[0][:6]:
        for n2 in top_per_pos[1][:6]:
            if n2 <= n1: continue
            for n3 in top_per_pos[2][:6]:
                if n3 <= n2: continue
                for n4 in top_per_pos[3][:6]:
                    if n4 <= n3: continue
                    for n5 in top_per_pos[4][:6]:
                        if n5 <= n4: continue
                        
                        ticket = [n1, n2, n3, n4, n5]
                        score = sum(pos_freq[i][ticket[i]] for i in range(5))
                        
                        decades = len(set(n // 10 for n in ticket))
                        consecutive = sum(1 for i in range(4) if ticket[i+1] - ticket[i] == 1)
                        
                        if decades < 3 or consecutive > 1:
                            continue
                        
                        if score > best_score:
                            best_ticket = ticket
                            best_score = score
    
    bonus_freq = Counter()
    for draw in draws:
        bonus = draw.get('bonus')
        if bonus:
            bonus_freq[bonus] += 1
    top_bonuses = [b for b, _ in bonus_freq.most_common(3)]
    
    return {'main': best_ticket, 'bonus': top_bonuses[0] if top_bonuses else 1, 'bonus_tied': top_bonuses, 'score': best_score}

print('='*60)
print('NEW OPTIMAL TICKETS (Pure Position Frequency)')
print('='*60)

current = {
    'l4l': [1, 7, 17, 33, 46],
    'la': [2, 15, 21, 33, 52],
    'pb': [4, 11, 35, 61, 69],
    'mm': [18, 21, 27, 42, 68]
}

for lottery in ['l4l', 'la', 'pb', 'mm']:
    draws = load_draws(lottery)
    if not draws:
        print(f'{lottery.upper()}: No data')
        continue
    
    result = calculate_optimal_ticket(lottery, draws)
    if result:
        old = current[lottery]
        new = result['main']
        changed = old != new
        status = 'YES - DIFFERENT!' if changed else 'No (same ticket)'
        print(f"{lottery.upper()}: {result['main']} + {result['bonus']} (score: {result['score']})")
        print(f"   Current: {old}")
        print(f"   Changed: {status}")
        print()
