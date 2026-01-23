@echo off
echo ============================================================
echo MASTER JACKPOT HUNTER SYSTEM
echo ============================================================
echo.
echo This system continuously hunts for optimal jackpot tickets using:
echo - All validated patterns from walk-forward backtesting
echo - Position frequency analysis
echo - Past winner exclusions (no 5/5 has EVER repeated)
echo - Hot 3-combo analysis (these DO repeat)
echo - Mod-512 filtering for RNG lotteries
echo.
echo Press Ctrl+C to stop at any time.
echo.
cd /d "%~dp0"

echo Running single pass first...
python MASTER_JACKPOT_SYSTEM.py --iterations 50000

echo.
echo ============================================================
echo Results saved to data\master_jackpot_tickets.json
echo ============================================================
echo.
pause
