import asyncio
import aiohttp
import json
import dotenv
import os
from datetime import datetime
from sleeping import run_daily_at_946am
from tools import filter_tickers
from nasdaq import get_nasdaq_tickers_sync
dotenv.load_dotenv()
# Replace these with your actual credentials
POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY")
DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL")
USE_TIMER: bool = os.getenv("USE_TIMER") != "False"
LOOP: bool = os.getenv("LOOP") != "False"
# DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1347713815273406514/Ur4ZD1C-NX9OWlYYn0Gec7Hmq-5tT9uaA4FrJPd_VlNk08ClTsakp7fhoreeUKmnO2Hs"

# Define RSI limits
RSI_OVERBOUGHT = 70  # Upper limit
RSI_OVERSOLD = 30    # Lower limit

# List of stock tickers to check
STOCK_TICKERS = []

# Async function to get the latest RSI for a given ticker
async def get_latest_rsi(session, ticker):
    url = (
        f"https://api.polygon.io/v1/indicators/rsi/{ticker}"
        f"?timespan=day&adjusted=true&window=14&series_type=close"
        f"&order=desc&limit=1&apiKey={POLYGON_API_KEY}"
    )
    
    print(f"Fetching RSI for {ticker}: {url}")
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

# Async function to send Discord webhook embed with all perspectives
async def send_discord_webhook(perspectives):
    if not perspectives:
        print("No perspectives to send.")
        return
    
    # Initialize content for oversold mentions (kept under 2000 chars)
    content = "**Oversold Alerts:**\n"
    oversold_tickers = [t for t, r, s, _ in perspectives if s == "Oversold"]
    if oversold_tickers:
        content += ", ".join(oversold_tickers) + "\n"
    else:
        content += "None\n"
    
    # Ensure content stays within Discord's 2000 character limit for the content field
    if len(content) > 1900:  # Leave some buffer
        content = content[:1897] + "..."

    # Create embeds for all perspectives (max 10 due to Discord limit)
    embeds = []
    for i, (ticker, rsi, status, timestamp) in enumerate(perspectives):
        if i >= 10:  # Discord limit: 10 embeds per message
            print(f"Warning: Exceeded 10 embeds, skipping {ticker} and beyond.")
            break
        
        date = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        color = 0xFF5555 if status == "Overbought" else 0x55FF55  # Softer red/green tones
        
        # Enhanced embed with fields and emojis
        embed = {
            "title": f"{ticker} RSI Alert 📈" if status == "Overbought" else f"{ticker} RSI Alert 📉",
            "description": f"Here's the latest RSI status for **{ticker}**",
            "color": color,
            "fields": [
                {"name": "📊 RSI Value", "value": f"`{rsi:.2f}`", "inline": True},
                {"name": "⚠️ Status", "value": f"**{status}**", "inline": True},
                {"name": "📅 Date", "value": date, "inline": False}
            ],
            "footer": {"text": "Powered by Polygon.io | RSI Bot"},
            "timestamp": datetime.utcnow().isoformat(),
            "thumbnail": {
                "url": "https://i.imgur.com/4M34hi2.png"  # Same as avatar, can be customized
            }
        }
        embeds.append(embed)

    # Customize webhook appearance
    payload = {
        "username": "RSI Bot",
        "avatar_url": "https://i.imgur.com/4M34hi2.png",
        "content": content,
        "embeds": embeds
    }

    # Ensure total payload size is under 6000 characters
    payload_str = json.dumps(payload)
    if len(payload_str) > 6000:
        print("Payload exceeds 6000 characters, trimming embeds...")
        embeds = embeds[:5]  # Reduce to 5 embeds as a fallback
        payload["embeds"] = embeds
        payload_str = json.dumps(payload)
        if len(payload_str) > 6000:
            print("Still too large, sending minimal version.")
            payload = {"username": "RSI Bot", "content": content[:1900]}

    # Send the webhook
    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_WEBHOOK_URL, json=payload) as response:
            if response.status == 204:
                print("Webhook sent successfully with all perspectives")
            else:
                print(f"Failed to send webhook: {response.status}")

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
            
            if rsi > RSI_OVERBOUGHT:
                perspectives.append((ticker, rsi, "Overbought", timestamp))
            elif rsi < RSI_OVERSOLD:
                perspectives.append((ticker, rsi, "Oversold", timestamp))
            else:
                print(f"{ticker}: RSI {rsi:.2f} is within normal range")
    
    # Send all perspectives in one webhook
    await send_discord_webhook(perspectives)


async def run():
    global STOCK_TICKERS
    STOCK_TICKERS = get_nasdaq_tickers_sync()
    print(STOCK_TICKERS)
    STOCK_TICKERS = filter_tickers(STOCK_TICKERS)[:1000]
    if not STOCK_TICKERS:
        print("No tickers fetched, exiting.")
        return
    
    print(f"Checking RSI for {len(STOCK_TICKERS)} tickers on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await check_rsi_and_alert(STOCK_TICKERS)

# Run the script
async def main():
    ran_once = False
    while not ran_once or LOOP:
        if USE_TIMER:
            await run_daily_at_946am(run)
        else:
            await run()
        ran_once = True


if __name__ == "__main__":
    asyncio.run(main())