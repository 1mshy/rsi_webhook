
from datetime import datetime, timedelta
import asyncio

# Function to calculate seconds until next 9:46 AM
def seconds_until_946am():
    now = datetime.now()
    target = now.replace(hour=9, minute=46, second=0, microsecond=0)
    
    # If it's past 9:46 AM today, schedule for tomorrow
    if now > target:
        target += timedelta(days=1)
    
    # Calculate seconds until the target time
    delta = (target - now).total_seconds()
    return delta if delta > 0 else delta + 86400  # 86400 seconds = 1 day

# Async scheduler function
async def run_daily_at_946am(func):
    while True:
        # Calculate delay until next 9:46 AM
        delay = seconds_until_946am()
        print(f"Waiting {delay:.2f} seconds or {delay//3600:.2f} hours until next run at 9:46 AM...")
        await asyncio.sleep(delay)
        
        # Run the main logic
        try:
            await func()
        except Exception as e:
            print(f"Error during execution: {str(e)}")
        
        # Wait briefly before recalculating to avoid immediate re-run
        await asyncio.sleep(60)  # Sleep 1 minute to ensure we pass 9:46 AM