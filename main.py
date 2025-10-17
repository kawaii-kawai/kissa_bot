# main.py
import os
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
