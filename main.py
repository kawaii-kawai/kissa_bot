import os
import asyncio
import threading
import discord
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS  # ← 追加
from datetime import datetime, timedelta

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))  # チャンネル指定用

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ===== 商品マッピング =====
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

COFFEE_CHANNEL = 1433338797810253904

# ===== Discordイベント =====
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == "!ping":
        await message.channel.send("Pong!")

# ===== API: /api/notify =====
@app.route('/api/notify', methods=['POST'])
def notify():
    data = request.json
    text = data.get("message", "No message provided.")

    async def send_message():
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"🔔 API通知: {text}")

    asyncio.run_coroutine_threadsafe(send_message(), client.loop)
    return jsonify({"status": "ok", "message": text})


# ===== API: /api/order =====
@app.route('/api/order', methods=['POST'])
def order():
    data = request.json
    order_data = data.get("order") if "order" in data else data
    if not isinstance(order_data, dict) or "items" not in order_data:
        return jsonify({"error": "Invalid order format"}), 400
    
    async def send_order():
        channel = client.get_channel(CHANNEL_ID)
        if not channel:
            print("⚠️ Discord channel not found.")
            return

        # --- 注文概要メッセージ ---
        orderNumber = order_data.get("orderNumber", "N/A")
        tableNumber = order_data.get("tableNumber", "N/A")
        orderType = order_data.get("orderType", "N/A")
        customerCount = order_data.get("customerCount", "N/A")

        header = (
            f"@kawaii_kawai\n"
            f"🧾 **新しい注文を受け付けました！**\n"
            f"> 通し番号: **{orderNumber}**\n"
            f"> 席番号: **{tableNumber}**\n"
            f"> 注文タイプ: **{orderType}**\n"
            f"> 人数: **{customerCount}**"
        )

        # --- 商品リスト ---
        item_lines = []
        coffee_count = 0
        for item in order_data["items"]:
            product_id = item.get("product")
            quantity = item.get("quantity", 1)
            name = item_mapping.get(product_id, "不明な商品")
            item_lines.append(f"> {name}: {quantity}")
            if name == "ドリップコーヒー":
                coffee_count += quantity

        item_text = "\n".join(item_lines)
        message = f"{header}\n\n{item_text}"

        try:
            await channel.send(message)
        except Exception as e:
            print(f"⚠️ Failed to send message: {e}")
        
        if coffee_count > 0:
            coffee_channel = client.get_channel(COFFEE_CHANNEL)
            if coffee_channel:
                created_at_str = order_data.get("createdAt")
                if created_at_str:
                    # UTC → 日本時間 (JST = UTC+9)
                    try:
                        utc_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        jst_time = utc_time + timedelta(hours=9)
                        time_str = jst_time.strftime("%d %H:%M")
                    except Exception:
                        time_str = created_at_str
                else:
                    time_str = "不明な時刻"

                msg = f"コーヒー注文: {coffee_count}個\n時刻: {time_str}"
                try:
                    await coffee_channel.send(msg)
                except Exception as e:
                    print(f"⚠️ Failed to send coffee info: {e}")


    # 非同期処理として送信
    asyncio.run_coroutine_threadsafe(send_order(), client.loop)
    return jsonify({"message": "Order sent to Discord"}), 200


# ===== Flaskサーバー =====
@app.route('/')
def home():
    return "✅ Bot is running."

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ===== 実行 =====
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    client.run(TOKEN)
