"""
Check what day Jan 8, 2026 is and which lotteries should have draws
"""

from datetime import datetime

jan8 = datetime(2026, 1, 8)
print(f"January 8, 2026 is: {jan8.strftime('%A')}")
print(f"Weekday number: {jan8.weekday()} (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun)")
print()

# L4L draws daily at 9:38 PM CT
print("L4L (Lucky for Life):")
print("  Schedule: DAILY at 9:38 PM CT")
print("  Latest should be: Jan 7, 2026 (or Jan 8 if after midnight)")
print()

# LA draws Mon/Wed/Sat at 10:00 PM CT
print("Lotto America:")
print("  Schedule: Mon/Wed/Sat at 10:00 PM CT")
if jan8.weekday() in [0, 2, 5]:  # Mon=0, Wed=2, Sat=5
    print("  ✓ DRAW DAY - Should have Jan 6 latest (waiting for tonight's draw)")
else:
    print("  ✗ Not a draw day")
print()

# PB draws Mon/Wed/Sat at 9:59 PM CT
print("Powerball:")
print("  Schedule: Mon/Wed/Sat at 9:59 PM CT")
if jan8.weekday() in [0, 2, 5]:
    print("  ✓ DRAW DAY - Should have Jan 6 latest (waiting for tonight's draw)")
else:
    print("  ✗ Not a draw day")
print()

# MM draws Tue/Fri at 10:00 PM CT
print("Mega Millions:")
print("  Schedule: Tue/Fri at 10:00 PM CT")
if jan8.weekday() in [1, 4]:  # Tue=1, Fri=4
    print("  ✓ DRAW DAY")
else:
    print("  ✗ Not a draw day - Last draw was Jan 7 (Tuesday)")
print()

print("EXPECTED LATEST DRAWS:")
print("- L4L: Jan 7, 2026")
print("- LA: Jan 6, 2026 (Mon) - Jan 8 draw happens tonight")
print("- PB: Jan 6, 2026 (Mon) - Jan 8 draw happens tonight")
print("- MM: Jan 7, 2026 (Tue)")
