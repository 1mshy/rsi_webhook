
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
            form_data.add_field("username", "RSI Bot")
            form_data.add_field("avatar_url", "https://i.imgur.com/4M34hi2.png")
            form_data.add_field('file', file, filename='image.png', content_type='image/png')
            async with session.post(DISCORD_WEBHOOK_URL, data=form_data) as response:
                if response.status == 204:
                    print("Webhook sent successfully with all perspectives")
                else:
                    print(f"Failed to send webhook: {response.status}")
                    

# Async function to send a compact Discord webhook with all perspectives
async def send_discord_webhook(perspectives):
    if not perspectives:
        print("No perspectives to send.")
        return
    
    # Compact content for oversold tickers (under 2000 chars)
    oversold = [t for t, _, s, _ in perspectives if s == "Oversold"]
    content = f"**Oversold:** {', '.join(oversold) if oversold else 'None'}\n"

    if len(content) > 1900:  # Buffer for Discord's 2000 char limit
        content = content[:1897] + "..."

    # Single embed for all perspectives (max 10 entries)
    embed = {
        "title": "RSI Alerts",
        "description": "Latest RSI statuses:",
        "color": 0x55FF55,  # Default green, adjusted below if needed
        "fields": [],
        "footer": {"text": "RSI Bot | Polygon.io"},
        "timestamp": datetime.utcnow().isoformat()
    }

    # Add up to 10 perspectives to a single embed
    for i, (ticker, rsi, status, timestamp) in enumerate(perspectives):
        if i == 0 and status == "Overbought":
            embed["color"] = 0xFF5555  # Red if first is overbought
        date = datetime.fromtimestamp(timestamp / 1000).strftime("%m-%d %H:%M")
        field = {
            "name": f"{ticker} {'📈' if status == 'Overbought' else '📉'}",
            "value": f"RSI: `{rsi:.1f}` | {status}",
            "inline": True
        }
        embed["fields"].append(field)

    # if len(perspectives) > 10:
    #     embed["footer"]["text"] += f" | {len(perspectives) - 10} more not shown"

    # Minimal payload
    payload = {
        "username": "RSI Bot",
        "content": content,
        "embeds": [embed] if embed["fields"] else []
    }

    # Check size and trim if necessary
    payload_str = json.dumps(payload)
    if len(payload_str) > 6000:
        print("Payload too large, trimming...")
        embed["fields"] = embed["fields"][:5]  # Limit to 5 entries
        payload["embeds"] = [embed]
        payload_str = json.dumps(payload)
        if len(payload_str) > 6000:
            payload = {"username": "RSI Bot", "content": content[:1900]}

    # Send the webhook
    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_WEBHOOK_URL, json=payload) as response:
            print("Webhook sent successfully" if response.status == 204 else f"Failed: {response.status}")