"""
Simple Flask server for Lottery Tracker
Serves data from JSON files, no complex logic
"""

from flask import Flask, jsonify, send_from_directory
import json
import os
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/latest')
def get_latest():
    """Get latest draw and jackpot for all 4 lotteries."""
    try:
        result = {}
        
        # Load each lottery's latest draw
        for lottery in ['l4l', 'la', 'pb', 'mm']:
            file_path = DATA_DIR / f"{lottery}.json"
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Get most recent draw (first in array since they're sorted newest first)
                latest_draw = data['draws'][0] if data['draws'] else None
                result[lottery.upper()] = {
                    'name': data.get('name') or data.get('lottery', lottery.upper()),
                    'latest': latest_draw,
                    'lastUpdated': data.get('lastUpdated', '')
                }
        
        # Load jackpots
        jackpot_path = DATA_DIR / "jackpots.json"
        with open(jackpot_path, 'r') as f:
            jackpots = json.load(f)
        
        # Merge jackpot info into result
        for lottery in ['L4L', 'LA', 'PB', 'MM']:
            if lottery in jackpots:
                result[lottery]['jackpot'] = jackpots[lottery]
        
        result['timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in /api/latest: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<lottery>')
def get_history(lottery):
    """Get full draw history for one lottery."""
    try:
        file_path = DATA_DIR / f"{lottery.lower()}.json"
        with open(file_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': f'Lottery {lottery} not found'}), 404
    except Exception as e:
        print(f"Error in /api/history/{lottery}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Manually trigger data refresh."""
    try:
        import updater
        results = updater.update_all()
        return jsonify(results)
    except Exception as e:
        print(f"Error in /api/refresh: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🎰 Lottery Tracker Server Starting...")
    print(f"📁 Data directory: {DATA_DIR}")
    print(f"🌐 Server running at: http://localhost:8000")
    print(f"Press Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=8000, debug=False)
