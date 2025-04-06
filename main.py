import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque
import time
import os
from flask import Flask
from threading import Thread

# Получаем токен бота из переменной окружения
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'default_search': 'auto',
    'noplaylist': True,
    'extract_flat': False,
}

queue = deque()
autoplay = False
loop_mode = "off"  # "off", "track", "queue"
now_playing = None
volume = 0.5
admin_roles = ["Admin"]  # Customize this with your server's admin roles

def is_admin():
    async def predicate(ctx):
        return any(role.name in admin_roles for role in ctx.author.roles)
    return commands.check(predicate)

# Flask приложение для работы с веб-сервером
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')

async def play_next(ctx):
    global now_playing
    if loop_mode == "track" and now_playing:
        queue.appendleft(now_playing['webpage_url'])

    if loop_mode == "queue" and now_playing:
        queue.append(now_playing['webpage_url'])

    if queue:
        url = queue.popleft()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info['url']
            now_playing = info

        vc = ctx.voice_client
        vc.play(discord.FFmpegPCMAudio(stream_url), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        vc.source = discord.PCMVolumeTransformer(vc.source)
        vc.source.volume = volume

        embed = discord.Embed(title="🎵 Now Playing", description=info['title'], color=discord.Color.orange())
        embed.add_field(name="Link", value=info.get('webpage_url', url), inline=False)
        embed.set_thumbnail(url=info.get('thumbnail', discord.Embed.Empty))
        await ctx.send(embed=embed)
    else:
        now_playing = None

# Переименовали команду help в custom_help
@bot.command(name="custom_help")
async def custom_help(ctx):
    commands_list = [cmd.name for cmd in bot.commands]
    await ctx.send("📚 Available commands: " + ", ".join(commands_list))

# Другие команды остаются такими же

# Запускаем веб-сервер в отдельном потоке
def run_discord_bot():
    bot.run(TOKEN)

# Запуск
if __name__ == "__main__":
    t1 = Thread(target=run_flask)
    t1.start()

    t2 = Thread(target=run_discord_bot)
    t2.start()
