
import asyncio
import aiohttp
import json
from datetime import datetime
import os
import dotenv


dotenv.load_dotenv()

DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL")

async def send_image(local_path):
    async with aiohttp.ClientSession() as session:
        with open(local_path, "rb") as file:
            form_data = aiohttp.FormData()
            form_data.add_field('file', file, filename='image.png', content_type='image/png')
            async with session.post(DISCORD_WEBHOOK_URL, data=form_data) as response:
                if response.status == 204:
                    print("Webhook sent successfully with all perspectives")
                else:
                    print(f"Failed to send webhook: {response.status}")
                    
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