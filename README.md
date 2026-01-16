# 🎰 Lottery Tracker

**Simple, cute, reliable lottery tracking for L4L, LA, Powerball, and Mega Millions**

## ✨ Features

- 🎯 **4 Major Lotteries**: Lucky for Life, Lotto America, Powerball, Mega Millions
- 📊 **Live Updates**: Auto-fetches from official sources every 30 minutes
- 💰 **Current Jackpots**: Always up-to-date prize amounts
- 🎨 **Cute UI**: Modern gradient design, smooth animations
- ⚡ **Fast Loading**: No spinners, shows cached data instantly
- 💾 **Reliable Storage**: All draws saved in simple JSON files

## 🚀 Quick Start

1. **Launch the server:**
   ```
   Double-click LAUNCH.bat
   ```

2. **Open in browser:**
   ```
   http://localhost:8000
   ```

That's it! The page will load instantly with cached data and auto-refresh.

## 📁 Project Structure

```
lottery-tracker/
├── data/
│   ├── l4l.json          # Lucky for Life draws
│   ├── la.json           # Lotto America draws
│   ├── pb.json           # Powerball draws
│   ├── mm.json           # Mega Millions draws
│   └── jackpots.json     # Current jackpots
├── server.py             # Flask server (port 8000)
├── updater.py            # Auto-fetch script
├── index.html            # Frontend UI
├── LAUNCH.bat            # One-click launcher
└── README.md             # This file
```

## 🔄 Manual Data Update

To manually fetch the latest draws:

```bash
python updater.py
```

Or click the "🔄 Refresh" button in the web UI.

## 🎨 Color Scheme

- **Lucky for Life**: Pink gradient (#FF69B4 → #FF1493)
- **Lotto America**: Blue gradient (#4169E1 → #1E90FF)
- **Powerball**: Red gradient (#DC143C → #B22222)
- **Mega Millions**: Gold gradient (#FFD700 → #FFA500)

## 📡 Data Sources (Official)

- **L4L**: Connecticut Lottery RSS Feed
- **LA**: Iowa Lottery Website
- **PB**: NY State Open Data (CSV)
- **MM**: NY State Open Data (CSV)

## 🛠️ API Endpoints

- `GET /` - Main page
- `GET /api/latest` - Latest draws + jackpots for all 4 lotteries
- `GET /api/history/<lottery>` - Full draw history (l4l, la, pb, mm)
- `POST /api/refresh` - Manually trigger data update

## ✅ Success Criteria

- ✅ All 4 lotteries display correctly
- ✅ Data updates automatically
- ✅ Page loads in <1 second
- ✅ Never shows loading spinner
- ✅ Cute modern design
- ✅ Works offline with cached data
- ✅ One-click launch

## 🐛 Troubleshooting

**Page won't load?**
- Make sure server is running (LAUNCH.bat)
- Check that port 8000 is not in use

**Data not updating?**
- Run `python updater.py` manually
- Check internet connection
- Verify official sources are accessible

**Missing Flask?**
```bash
pip install flask
```

---

Made with 💖 for easy lottery tracking
