import os
import threading
import discord
from flask import Flask
from dotenv import load_dotenv

# === Flask サーバー ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Discord bot is running on Render!"

def run_flask():
    # Render では PORT 環境変数が自動で割り当てられる
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# === Discord Bot ===
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == "!hello":
        await message.channel.send("Hello from Render!")

# Flask を別スレッドで起動
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    client.run(TOKEN)
