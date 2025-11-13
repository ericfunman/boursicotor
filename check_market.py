#!/usr/bin/env python
"""Check if market is open"""
from datetime import datetime
import pytz

paris_tz = pytz.timezone('Europe/Paris')
paris_time = datetime.now(paris_tz)

print(f'Current time in Paris: {paris_time.strftime("%H:%M:%S %Z")}')
print(f'Euronext open time: 09:00 CET')
print(f'Euronext close time: 17:30 CET')

if 9 <= paris_time.hour < 17:
    print('✅ Market is OPEN (or closing soon)')
elif paris_time.hour == 17 and paris_time.minute <= 30:
    print('⚠️ Market is CLOSING (< 30min to close)')
else:
    print('❌ Market is CLOSED - No intraday data available')
