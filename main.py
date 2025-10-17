# main.py
import os
import asyncio
import threading
import discord
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))  # チャンネル指定用

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

app = Flask(__name__)

item_mapping = {
    "686a7cb3cbfdbb7438d746bc": "クロックムッシュ",
    "686a7ce0cbfdbb7438d74e73": "チョコクロ",
    "686a7cfecbfdbb7438d74e75": "ベリーパフェ",
    "686a7d03cbfdbb7438d74e77": "抹茶パフェ",
    "686a7d10cbfdbb7438d74e79": "コンソメスープ",
    "686a7d1ccbfdbb7438d74e7b": "小倉トースト",
    "686a7d24cbfdbb7438d74e7d": "クラフトコーラ",
    "686a7d88cbfdbb7438d74e7f": "ドリップコーヒー",
    "686a7d90cbfdbb7438d74e81": "リンゴジュース",
    "686a7d98cbfdbb7438d74e83": "紅茶（ホット）",
    "68d7563169cb686cf32bff58": "アイスコーヒー",
}

# Discordイベント
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == "!ping":
        await message.channel.send("Pong!")

@app.route('/api/notify', methods=['POST'])
def notify():
    data = request.json
    text = data.get("message", "No message provided.")

    async def send_message():
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"🔔 API通知: {text}")

    client.loop.create_task(send_message())
    return jsonify({"status": "ok", "message": text})

@app.route('/api/order', methods=['POST'])
def order():
    data = request.json
    order_data = data.get("order") if "order" in data else data
    if not isinstance(order_data, dict) or "items" not in order_data:
        return jsonify({"error": "Invalid order format"}), 400
    
    try:
        for item in order_data["items"]:
            product_id = item.get("product")
            quantity = item.get("quantity")

            if product_id not in item_mapping:
                continue

            product_name = item_mapping[product_id]
            message = f">>> 商品: **{product_name}**\n数量: **{quantity}**"
            channel = client.get_channel(CHANNEL_ID)

            if not channel: continue
            future = asyncio.run_coroutine_threadsafe(channel.send(message), client.loop)
            try:
                future.result(timeout=5)
            except Exception as e:
                print(f"⚠️ Failed to send message: {e}")

        return jsonify({"message": "All messages sent successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
           


# Flaskサーバー
@app.route('/')
def home():
    return "✅ Bot is running."

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    client.run(TOKEN)
