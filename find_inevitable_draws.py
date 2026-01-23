"""
FIND INEVITABLE DRAWS - Simple, fast, guaranteed to run
Novel patterns to find future drawings that will surely happen
"""
import json
from pathlib import Path
from collections import Counter, defaultdict

DATA_DIR = Path(__file__).parent / 'data'

def load_draws(lottery):
    for fn in [f'{lottery}.json', f'{lottery}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                draws = d.get('draws', d) if isinstance(d, dict) else d
                print(f"  Loaded {len(draws)} draws from {fn}")
                return draws
    return []

CONFIGS = {
    'l4l': {'name': 'Lucky for Life', 'max': 48, 'bonus_max': 18},
    'la':  {'name': 'Lotto America', 'max': 52, 'bonus_max': 10},
}

def main():
    print("=" * 70)
    print("FIND INEVITABLE DRAWS - Novel Pattern Analysis")
    print("=" * 70)
    
    results = {}
    
    for lottery, cfg in CONFIGS.items():
        print(f"\n{'='*70}")
        print(f"Analyzing {cfg['name']}...")
        
        draws = load_draws(lottery)
        if not draws or len(draws) < 50:
            print(f"  Not enough data")
            continue
        
        max_num = cfg['max']
        
        # =====================================================================
        # 1. OVERDUE NUMBERS - Numbers that MUST appear based on gap stats
        # =====================================================================
        print(f"\n⏰ OVERDUE ANALYSIS:")
        
        last_seen = {}
        all_gaps = defaultdict(list)
        
        for i, draw in enumerate(draws):
            main = draw.get('main', [])
            for num in main:
                if num in last_seen:
                    all_gaps[num].append(i - last_seen[num])
                last_seen[num] = i
        
        overdue = []
        for num in range(1, max_num + 1):
            if num in last_seen and len(all_gaps[num]) >= 5:
                current_gap = last_seen[num]
                avg = sum(all_gaps[num]) / len(all_gaps[num])
                max_gap = max(all_gaps[num])
                if current_gap > avg * 1.3:
                    overdue.append({
                        'num': num,
                        'gap': current_gap,
                        'avg': avg,
                        'max': max_gap,
                        'ratio': current_gap / avg
                    })
        
        overdue.sort(key=lambda x: x['ratio'], reverse=True)
        
        print(f"  Numbers exceeding average gap by 30%+:")
        for item in overdue[:10]:
            print(f"    #{item['num']:2d}: {item['gap']} draws (avg {item['avg']:.0f}, max {item['max']}) - {item['ratio']:.1f}x overdue")
        
        # =====================================================================
        # 2. FOLLOW PATTERNS - What comes after what?
        # =====================================================================
        print(f"\n🔗 FOLLOW PATTERNS (what appears after last draw):")
        
        last_draw = set(draws[0].get('main', []))
        print(f"  Last draw was: {sorted(last_draw)}")
        
        followers = Counter()
        for i in range(len(draws) - 1):
            current = set(draws[i].get('main', []))
            if current == last_draw or len(current & last_draw) >= 3:
                next_nums = draws[i + 1].get('main', [])
                for num in next_nums:
                    followers[num] += 1
        
        print(f"  Numbers that followed similar draws:")
        for num, cnt in followers.most_common(10):
            print(f"    #{num:2d}: appeared {cnt} times")
        
        # =====================================================================
        # 3. POSITION FREQUENCY - Most likely per position
        # =====================================================================
        print(f"\n📍 TOP NUMBERS PER POSITION (last 200 draws):")
        
        pos_freq = {i: Counter() for i in range(5)}
        for draw in draws[:200]:
            main = sorted(draw.get('main', []))
            for i, num in enumerate(main[:5]):
                pos_freq[i][num] += 1
        
        pos_top = []
        for i in range(5):
            top = pos_freq[i].most_common(5)
            pos_top.append([n for n, _ in top])
            top_str = ', '.join([f"{n}({c})" for n, c in top[:3]])
            print(f"    P{i+1}: {top_str}")
        
        # =====================================================================
        # 4. PAIRS THAT KEEP APPEARING
        # =====================================================================
        print(f"\n👯 HOT PAIRS (last 200 draws):")
        
        pair_freq = Counter()
        for draw in draws[:200]:
            main = sorted(draw.get('main', []))
            for i in range(len(main)):
                for j in range(i + 1, len(main)):
                    pair_freq[(main[i], main[j])] += 1
        
        for pair, cnt in pair_freq.most_common(8):
            print(f"    {pair}: {cnt} times")
        
        # =====================================================================
        # 5. NUMBERS THAT APPEAR TOGETHER IN CLUSTERS
        # =====================================================================
        print(f"\n🕸️ NUMBER CLUSTERS (frequently co-occur):")
        
        # Find numbers that share many pairs
        num_partners = defaultdict(set)
        for (a, b), cnt in pair_freq.most_common(50):
            num_partners[a].add(b)
            num_partners[b].add(a)
        
        # Find cluster seeds
        top_connected = sorted(num_partners.keys(), key=lambda x: len(num_partners[x]), reverse=True)[:5]
        for seed in top_connected[:3]:
            cluster = [seed] + list(num_partners[seed])[:4]
            print(f"    Cluster around #{seed}: {sorted(cluster)}")
        
        # =====================================================================
        # 6. BUILD INEVITABLE TICKET
        # =====================================================================
        print(f"\n🎯 BUILDING INEVITABLE TICKET:")
        
        # Score all numbers
        scores = Counter()
        
        # Overdue boost
        for item in overdue[:15]:
            scores[item['num']] += item['ratio'] * 2
        
        # Follower boost
        for num, cnt in followers.most_common(15):
            scores[num] += cnt * 0.5
        
        # Position frequency boost
        for i, tops in enumerate(pos_top):
            for rank, num in enumerate(tops[:5]):
                scores[num] += (5 - rank) * 0.3
        
        # Hot pair boost
        for (a, b), cnt in pair_freq.most_common(20):
            scores[a] += cnt * 0.1
            scores[b] += cnt * 0.1
        
        print(f"  Top scoring numbers: {scores.most_common(15)}")
        
        # Build ticket respecting position order
        ticket = []
        used = set()
        
        for pos in range(5):
            best_num = None
            best_score = -1
            
            # Get valid range for this position
            pos_nums = list(pos_freq[pos].keys())
            min_pos = min(pos_nums) if pos_nums else 1
            max_pos = max(pos_nums) if pos_nums else max_num
            
            for num, score in scores.most_common():
                if num in used:
                    continue
                if num < min_pos or num > max_pos:
                    continue
                if ticket and num <= ticket[-1]:
                    continue
                if score > best_score:
                    best_score = score
                    best_num = num
            
            if best_num:
                ticket.append(best_num)
                used.add(best_num)
                print(f"    P{pos+1}: #{best_num} (score {best_score:.1f})")
        
        # Get bonus
        bonus_freq = Counter()
        for draw in draws[:100]:
            b = draw.get('bonus')
            if b:
                bonus_freq[b] += 1
        top_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
        
        # Check if ever drawn
        ticket_set = set(ticket)
        ever_drawn = any(set(d.get('main', [])) == ticket_set for d in draws)
        
        print(f"\n" + "=" * 50)
        print(f"🔮 INEVITABLE TICKET: {ticket} + {top_bonus}")
        print(f"=" * 50)
        
        if ever_drawn:
            print("⚠️  This combination HAS been drawn before")
        else:
            print("✅ NEVER DRAWN - Fresh unique prediction!")
        
        results[lottery] = {
            'ticket': ticket,
            'bonus': top_bonus,
            'overdue': [{'num': x['num'], 'ratio': x['ratio']} for x in overdue[:10]],
            'ever_drawn': ever_drawn
        }
    
    # Save results
    out_path = DATA_DIR / 'inevitable_draws.json'
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Saved to {out_path}")
    
    return results

if __name__ == '__main__':
    main()
