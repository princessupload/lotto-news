"""
Automatic scheduler for lottery data and jackpot updates
Runs in background alongside server
"""

import time
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent

def update_all():
    """Run the dual-source updater."""
    print(f"\n{'='*60}")
    print(f"🔄 AUTO-UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Run dual-source updater (handles both drawings AND jackpots)
    try:
        subprocess.run(['python', str(BASE_DIR / 'dual_source_updater.py')], check=True)
        print("✅ Update complete")
    except Exception as e:
        print(f"Dual-source updater error: {e}")
        # Fallback to old updater if dual-source fails
        try:
            subprocess.run(['python', str(BASE_DIR / 'updater.py')], check=True)
            subprocess.run(['python', str(BASE_DIR / 'get_jackpots.py')], check=True)
        except Exception as e2:
            print(f"Fallback error: {e2}")

def run_scheduler():
    """Set up and run the scheduler."""
    print("=" * 60)
    print("LOTTERY TRACKER AUTO-SCHEDULER STARTED")
    print("=" * 60)
    print()
    print("📅 Schedule: Every 30 minutes")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Run immediately on start
    print("\n🚀 Running initial update...")
    update_all()
    
    # Keep running every 30 minutes
    while True:
        try:
            print(f"\n⏰ Next update in 30 minutes...")
            time.sleep(1800)  # 30 minutes
            update_all()
        except KeyboardInterrupt:
            print("\n\n⏹️ Scheduler stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Scheduler error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    run_scheduler()
