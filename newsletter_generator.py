#!/usr/bin/env python3
"""
Newsletter Generator - Matches Lottery Tracker App Styling
Generates embeddable HTML content for Patreon, Substack, or any website.
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'

# Oklahoma tax rate (24% federal + 4.75% state)
TOTAL_TAX_RATE = 0.2875

# Lottery configs
LOTTERY_CONFIG = {
    'l4l': {'name': 'Lucky for Life', 'emoji': '🍀', 'bonus_name': 'Lucky Ball'},
    'la':  {'name': 'Lotto America', 'emoji': '⭐', 'bonus_name': 'Star Ball'},
    'pb':  {'name': 'Powerball', 'emoji': '🔴', 'bonus_name': 'Powerball'},
    'mm':  {'name': 'Mega Millions', 'emoji': '💰', 'bonus_name': 'Mega Ball'}
}

def load_draws(lottery):
    """Load historical draws for a lottery."""
    for filename in [f'{lottery}_historical_data.json', f'{lottery}.json']:
        path = DATA_DIR / filename
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                return data.get('draws', [])
    return []

def load_jackpots():
    """Load current jackpot data."""
    path = DATA_DIR / 'jackpots.json'
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

def format_money(amount):
    """Format money with appropriate suffix."""
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:,}"

def calculate_after_tax(cash_value):
    """Calculate after-tax amount for Oklahoma winner."""
    if not cash_value or cash_value <= 0:
        return 0
    return int(cash_value * (1 - TOTAL_TAX_RATE))

def generate_position_pools(draws, main_count=5):
    """Generate position frequency pools from historical draws."""
    from collections import Counter
    position_counters = [Counter() for _ in range(main_count)]
    
    for draw in draws[:400]:  # Use last 400 draws
        main_nums = sorted(draw.get('main', []))
        for i, num in enumerate(main_nums):
            if i < main_count:
                position_counters[i][num] += 1
    
    pools = []
    for counter in position_counters:
        top_nums = [num for num, _ in counter.most_common(8)]
        pools.append(top_nums)
    
    return pools

def generate_newsletter_html():
    """Generate beautiful newsletter HTML matching lottery tracker app style."""
    
    # Load all data
    draws_by_lottery = {}
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        draws_by_lottery[lottery] = load_draws(lottery)
    
    jackpots = load_jackpots()
    current_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    current_date = datetime.now().strftime('%B %d, %Y')
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lottery Newsletter - {current_date}</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Cormorant+Garamond:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Cormorant Garamond', Georgia, serif;
            background: linear-gradient(135deg, #F9A8D4 0%, #B0E0E6 50%, #ff75cc 100%);
            min-height: 100vh;
            padding: 20px;
            color: #000000;
        }}
        
        .newsletter-container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border: 4px solid #ff47bb;
            border-radius: 25px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(255, 71, 187, 0.4);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #F9A8D4;
        }}
        
        h1 {{
            font-family: 'Playfair Display', serif;
            background: linear-gradient(135deg, #ff47bb 0%, #ff75cc 50%, #F9A8D4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.5em;
            margin-bottom: 10px;
            letter-spacing: 2px;
        }}
        
        .date {{
            color: #ff47bb;
            font-size: 1.2em;
            font-style: italic;
        }}
        
        .section {{
            margin: 25px 0;
            padding: 20px;
            background: linear-gradient(135deg, #fff0f5 0%, #f0f8ff 100%);
            border-radius: 15px;
            border: 2px solid #F9A8D4;
        }}
        
        .section-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.5em;
            color: #ff47bb;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #B0E0E6;
        }}
        
        .lottery-card {{
            background: white;
            border: 3px solid #7DD3FC;
            border-radius: 15px;
            padding: 15px;
            margin: 15px 0;
            box-shadow: 0 4px 15px rgba(125, 211, 252, 0.3);
        }}
        
        .lottery-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .lottery-name {{
            font-family: 'Playfair Display', serif;
            font-size: 1.3em;
            color: #ff47bb;
        }}
        
        .jackpot-badge {{
            background: linear-gradient(135deg, #32CD32 0%, #228B22 100%);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .numbers {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            margin: 12px 0;
        }}
        
        .ball {{
            display: inline-flex;
            width: 42px;
            height: 42px;
            border-radius: 50%;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 16px;
            background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
            border: 3px solid #ff47bb;
            color: #ff47bb;
            box-shadow: 0 3px 10px rgba(255, 71, 187, 0.3);
        }}
        
        .ball.bonus {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            border-color: #FF8C00;
            color: #8B4513;
        }}
        
        .plus {{
            font-size: 1.5em;
            color: #ff47bb;
            margin: 0 5px;
        }}
        
        .draw-date {{
            font-size: 0.9em;
            color: #666;
            margin-top: 8px;
        }}
        
        .pool-section {{
            background: #fff9fc;
            border: 2px dashed #F9A8D4;
            border-radius: 12px;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .pool-title {{
            color: #ff47bb;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .pool-numbers {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .pool-num {{
            background: #B0E0E6;
            color: #006080;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 3px solid #F9A8D4;
            color: #888;
            font-size: 0.9em;
        }}
        
        .footer a {{
            color: #ff47bb;
            text-decoration: none;
        }}
        
        .cta-box {{
            background: linear-gradient(135deg, #ff47bb 0%, #ff75cc 100%);
            color: white;
            text-align: center;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
        }}
        
        .cta-box h3 {{
            font-family: 'Playfair Display', serif;
            font-size: 1.4em;
            margin-bottom: 10px;
        }}
        
        @media (max-width: 600px) {{
            .newsletter-container {{ padding: 15px; }}
            h1 {{ font-size: 1.8em; }}
            .ball {{ width: 36px; height: 36px; font-size: 14px; }}
        }}
    </style>
</head>
<body>
    <div class="newsletter-container">
        <div class="header">
            <h1>💖 LOTTERY NEWS 💖</h1>
            <p class="date">{current_date}</p>
        </div>
        
        <!-- LATEST DRAWINGS SECTION -->
        <div class="section">
            <h2 class="section-title">🎱 Latest Drawing Results</h2>
'''
    
    # Add latest drawings
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        config = LOTTERY_CONFIG[lottery]
        draws = draws_by_lottery.get(lottery, [])
        jp = jackpots.get(lottery, {})
        
        if draws:
            latest = draws[0]
            main_nums = sorted(latest.get('main', []))
            bonus = latest.get('bonus', '?')
            draw_date = latest.get('date', 'Unknown')
            
            # Jackpot info
            cash = jp.get('cash_value', 0)
            after_tax = calculate_after_tax(cash) if cash else 0
            jackpot_str = format_money(after_tax) if after_tax else 'N/A'
            
            balls_html = ''.join([f'<span class="ball">{n}</span>' for n in main_nums])
            
            html += f'''
            <div class="lottery-card">
                <div class="lottery-header">
                    <span class="lottery-name">{config['emoji']} {config['name']}</span>
                    <span class="jackpot-badge">💰 {jackpot_str} after tax</span>
                </div>
                <div class="numbers">
                    {balls_html}
                    <span class="plus">+</span>
                    <span class="ball bonus">{bonus}</span>
                    <span style="margin-left: 8px; color: #888; font-size: 0.9em;">{config['bonus_name']}</span>
                </div>
                <div class="draw-date">📅 Draw Date: {draw_date}</div>
            </div>
'''
    
    html += '''
        </div>
        
        <!-- NUMBER POOLS SECTION -->
        <div class="section">
            <h2 class="section-title">🎯 Build Your Own Ticket</h2>
            <p style="margin-bottom: 15px; color: #666;">Pick ONE number from each position pool to create your unique ticket. Don't play the same numbers as everyone else!</p>
'''
    
    # Add position pools for each lottery
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        config = LOTTERY_CONFIG[lottery]
        draws = draws_by_lottery.get(lottery, [])
        
        if draws:
            pools = generate_position_pools(draws)
            
            html += f'''
            <div class="pool-section">
                <div class="pool-title">{config['emoji']} {config['name']} Position Pools</div>
'''
            for i, pool in enumerate(pools):
                pool_html = ''.join([f'<span class="pool-num">{n}</span>' for n in pool])
                html += f'''
                <div style="margin: 8px 0;">
                    <strong style="color: #ff47bb;">Position {i+1}:</strong>
                    <div class="pool-numbers" style="display: inline-flex; margin-left: 10px;">{pool_html}</div>
                </div>
'''
            html += '''
            </div>
'''
    
    html += f'''
        </div>
        
        <!-- CTA BOX -->
        <div class="cta-box">
            <h3>✨ Want Daily Updates? ✨</h3>
            <p>Follow us on Twitch and YouTube for live analysis!</p>
            <p style="margin-top: 10px;">
                <a href="https://twitch.tv/princessupload" style="color: white; text-decoration: underline;">📺 Twitch</a> | 
                <a href="https://youtube.com/@princessuploadie" style="color: white; text-decoration: underline;">▶️ YouTube</a>
            </p>
        </div>
        
        <div class="footer">
            <p>💖 With love from Princess Upload 💖</p>
            <p style="margin-top: 10px; font-size: 0.8em;">
                🎰 For entertainment purposes only • Generated {current_time} CT (Oklahoma)
            </p>
        </div>
    </div>
</body>
</html>'''
    
    return html

def generate_embed_snippet():
    """Generate a simple HTML snippet that can be embedded in Patreon/Substack."""
    draws_by_lottery = {}
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        draws_by_lottery[lottery] = load_draws(lottery)
    
    jackpots = load_jackpots()
    current_date = datetime.now().strftime('%B %d, %Y')
    
    # Simple inline-styled HTML for embedding
    snippet = f'''<div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #fff0f5 0%, #f0f8ff 100%); border: 3px solid #ff47bb; border-radius: 15px;">
    <h2 style="color: #ff47bb; text-align: center; margin-bottom: 15px;">💖 LOTTERY UPDATE - {current_date} 💖</h2>
'''
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        config = LOTTERY_CONFIG[lottery]
        draws = draws_by_lottery.get(lottery, [])
        jp = jackpots.get(lottery, {})
        
        if draws:
            latest = draws[0]
            main_nums = sorted(latest.get('main', []))
            bonus = latest.get('bonus', '?')
            draw_date = latest.get('date', 'Unknown')
            
            cash = jp.get('cash_value', 0)
            after_tax = calculate_after_tax(cash) if cash else 0
            
            nums_str = ' - '.join(map(str, main_nums))
            
            snippet += f'''
    <div style="background: white; border: 2px solid #7DD3FC; border-radius: 10px; padding: 12px; margin: 10px 0;">
        <strong style="color: #ff47bb;">{config['emoji']} {config['name']}</strong>
        <span style="float: right; background: #32CD32; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em;">{format_money(after_tax)}</span>
        <div style="margin-top: 8px; font-size: 1.1em;">
            <strong>{nums_str}</strong> + <span style="background: #FFD700; padding: 2px 6px; border-radius: 50%;">{bonus}</span>
        </div>
        <div style="font-size: 0.85em; color: #666; margin-top: 5px;">📅 {draw_date}</div>
    </div>
'''
    
    snippet += '''
    <p style="text-align: center; margin-top: 15px; font-size: 0.9em; color: #666;">
        💖 <a href="https://twitch.tv/princessupload" style="color: #ff47bb;">Twitch</a> | 
        <a href="https://youtube.com/@princessuploadie" style="color: #ff47bb;">YouTube</a> 💖
    </p>
</div>'''
    
    return snippet

def main():
    """Generate newsletter files."""
    output_dir = Path(__file__).parent / 'newsletter_output'
    output_dir.mkdir(exist_ok=True)
    
    # Generate full HTML newsletter
    full_html = generate_newsletter_html()
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Save full newsletter
    newsletter_file = output_dir / f'newsletter_{date_str}.html'
    with open(newsletter_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"✅ Full newsletter saved: {newsletter_file}")
    
    # Also save as latest.html for easy access
    latest_file = output_dir / 'latest.html'
    with open(latest_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"✅ Latest newsletter saved: {latest_file}")
    
    # Generate embed snippet
    embed_html = generate_embed_snippet()
    embed_file = output_dir / 'embed_snippet.html'
    with open(embed_file, 'w', encoding='utf-8') as f:
        f.write(embed_html)
    print(f"✅ Embed snippet saved: {embed_file}")
    
    print(f"\n📋 TO USE:")
    print(f"   1. Open {latest_file} in browser to preview")
    print(f"   2. Copy contents of {embed_file} into Patreon/Substack HTML editor")
    print(f"   3. Newsletter auto-updates daily via GitHub Actions")

if __name__ == '__main__':
    main()
