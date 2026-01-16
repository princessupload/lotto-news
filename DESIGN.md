# 🎰 Lottery Tracker - Clean Rebuild Design

## Goals
1. **Reliable**: Never lose data, always show something
2. **Simple**: One updater, one server, one page
3. **Cute**: Modern pink/purple theme, smooth animations
4. **Fast**: Loads instantly, no loading spinners
5. **Accurate**: Official sources only, verify data

## Data Sources (Official Only)

### Lucky for Life (L4L)
- **Primary**: CT Lottery RSS - `https://www.ctlottery.org/Feeds/rssnumbers.xml`
- **Schedule**: Daily at 9:38 PM CT
- **Format**: 5 main (1-48) + Lucky Ball (1-18)

### Lotto America (LA)
- **Primary**: Iowa Lottery - `https://www.ialottery.com/games/lotto-america`
- **Schedule**: Mon/Wed/Sat at 10:00 PM CT
- **Format**: 5 main (1-52) + Star Ball (1-10)

### Powerball (PB)
- **Primary**: NY Open Data CSV - `https://data.ny.gov/api/views/d6yy-54nr/rows.csv`
- **Schedule**: Mon/Wed/Sat at 9:59 PM CT
- **Format**: 5 main (1-69) + Powerball (1-26)

### Mega Millions (MM)
- **Primary**: NY Open Data CSV - `https://data.ny.gov/api/views/5xaw-6ayf/rows.csv`
- **Schedule**: Tue/Fri at 10:00 PM CT
- **Format**: 5 main (1-70) + Mega Ball (1-25)

## Data Format (JSON)

```json
{
  "lottery": "L4L",
  "draws": [
    {"date": "2026-01-08", "main": [3,8,13,38,47], "bonus": 2},
    {"date": "2026-01-07", "main": [1,5,12,22,33], "bonus": 9}
  ],
  "lastUpdated": "2026-01-08T13:00:00"
}
```

## UI Design (Single Page)

### Header
- 🎰 **Lottery Tracker** logo (cute pink ticket icon)
- Last updated timestamp
- Refresh button

### Cards (4 lottery cards, responsive grid)

Each card shows:
```
┌─────────────────────────────┐
│ 🎯 Lucky for Life            │
│ ─────────────────────────── │
│ Latest: Jan 8, 2026         │
│ [3] [8] [13] [38] [47] 🌟2  │
│                             │
│ Jackpot: $7K/week for life  │
│ Next Draw: Tonight 9:38 PM  │
│                             │
│ [View History →]            │
└─────────────────────────────┘
```

### Color Scheme
- **L4L**: Pink gradient `#FF69B4 → #FF1493`
- **LA**: Blue gradient `#4169E1 → #1E90FF`
- **PB**: Red gradient `#DC143C → #B22222`
- **MM**: Gold gradient `#FFD700 → #FFA500`
- **Background**: Soft white `#FAFAFA`
- **Text**: Dark gray `#333333`

### Animations
- Smooth card hover (lift + shadow)
- Number balls bounce in on load
- Pulse on data update
- Smooth transitions (200ms ease)

## Backend API

### GET /api/latest
Returns all 4 lotteries' latest draws + jackpots:
```json
{
  "L4L": {"latest": {...}, "jackpot": "..."},
  "LA": {"latest": {...}, "jackpot": "..."},
  "PB": {"latest": {...}, "jackpot": "..."},
  "MM": {"latest": {...}, "jackpot": "..."},
  "lastUpdated": "2026-01-08T13:00:00"
}
```

### GET /api/history/:lottery
Returns full draw history for one lottery

### POST /api/refresh
Manually trigger data update

## Auto-Update Logic

**Every 30 minutes:**
1. Fetch from official sources
2. Validate format (correct number ranges)
3. Check if new (compare to last draw)
4. If new → append to JSON file
5. Update jackpots
6. Log success/failure

**Error Handling:**
- Source down? → Keep showing cached data
- Invalid data? → Skip update, alert in console
- Never crash, never show errors to user

## Development Steps

1. ✅ Design document (this file)
2. Create data files with current data
3. Build simple Flask server
4. Build auto-updater script
5. Create cute HTML/CSS/JS frontend
6. Test full cycle: update → save → display
7. Add launch script
8. Deploy and verify

## Success Criteria

- ✅ All 4 lotteries display correctly
- ✅ Data updates automatically
- ✅ Page loads in <1 second
- ✅ Never shows loading spinner
- ✅ Looks cute and modern
- ✅ Works offline with cached data
- ✅ One-click launch
