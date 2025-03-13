import asyncio
import aiohttp
import json
import dotenv
import os
from datetime import datetime
from sleeping import run_daily_at_946am
from tools import filter_tickers
from nasdaq import get_nasdaq_tickers_sync
from chrome_driver import request_heatmap_nasdaq
from discord import send_discord_webhook, send_image


dotenv.load_dotenv()


# Replace these with your actual credentials
POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY")
DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL")
USE_TIMER: bool = os.getenv("USE_TIMER") != "False"
LOOP: bool = os.getenv("LOOP") != "False"
SHOW_LOW_RSI: str = os.getenv("SHOW_LOW_RSI") != "False"
SHOW_HIGH_RSI: str = os.getenv("SHOW_HIGH_RSI") != "False"
# DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1347713815273406514/Ur4ZD1C-NX9OWlYYn0Gec7Hmq-5tT9uaA4FrJPd_VlNk08ClTsakp7fhoreeUKmnO2Hs"

# Define RSI limits
RSI_OVERBOUGHT = int(os.getenv("RSI_OVERBOUGHT"))  # Upper limit
RSI_OVERSOLD = int(os.getenv("RSI_OVERSOLD"))    # Lower limit

# List of stock tickers to check
STOCK_TICKERS = []

# Async function to get the latest RSI for a given ticker
async def get_latest_rsi(session, ticker):
    url = (
        f"https://api.polygon.io/v1/indicators/rsi/{ticker}"
        f"?timespan=day&adjusted=true&window=14&series_type=close"
        f"&order=desc&limit=1&apiKey={POLYGON_API_KEY}"
    )
    
    # print(f"Fetching RSI for {ticker}: {url}")
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data["status"] == "OK" and "results" in data and "values" in data["results"]:
                    latest_rsi = float(data["results"]["values"][0]["value"])
                    timestamp = int(data["results"]["values"][0]["timestamp"])
                    return ticker, latest_rsi, timestamp
                else:
                    print(f"Error fetching RSI for {ticker}: No valid data returned")
                    return ticker, None, None
            else:
                print(f"Error fetching RSI for {ticker}: {response.status}")
                return ticker, None, None
    except Exception as e:
        print(f"Exception while fetching RSI for {ticker}: {str(e)}")
        return ticker, None, None


# Main async function to check RSI and collect perspectives
async def check_rsi_and_alert(stock_tickers=STOCK_TICKERS):
    perspectives = []  # List to store all notable RSI perspectives
    
    async with aiohttp.ClientSession() as session:
        # Create tasks for all tickers
        tasks = [get_latest_rsi(session, ticker) for ticker in stock_tickers]
        results = await asyncio.gather(*tasks)
        
        # Process results and collect perspectives
        for ticker, rsi, timestamp in results:
            if rsi is None or timestamp is None:
                continue
            
            if SHOW_HIGH_RSI and rsi > RSI_OVERBOUGHT:
                perspectives.append((ticker, rsi, "Overbought", timestamp))
            elif SHOW_LOW_RSI and rsi < RSI_OVERSOLD:
                perspectives.append((ticker, rsi, "Oversold", timestamp))
            else:
                # print(f"Skipping {ticker}: RSI {rsi:.2f} is within normal range set")
                pass
    
    # Send all perspectives in one webhook
    await send_discord_webhook(perspectives)


async def run():
    global STOCK_TICKERS
    STOCK_TICKERS = get_nasdaq_tickers_sync()
    # print(STOCK_TICKERS)
    STOCK_TICKERS = filter_tickers(STOCK_TICKERS)[:1000]
    if not STOCK_TICKERS:
        print("No tickers fetched, exiting.")
        return
    
    print(f"Checking RSI for {len(STOCK_TICKERS)} tickers on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await check_rsi_and_alert(STOCK_TICKERS)

# Run the script
async def main():
    heatmap = request_heatmap_nasdaq()
    await send_image(heatmap)
    print("Send image of current heatmap")
    ran_once = False
    while not ran_once or LOOP:
        if USE_TIMER:
            await run_daily_at_946am(run)
        else:
            await run()
        ran_once = True


if __name__ == "__main__":
    asyncio.run(main())