import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque
import time
import os  # Импортируем библиотеку os для работы с переменными окружения

# Получаем токен бота из переменной окружения
TOKEN = os.getenv('DISCORD_TOKEN')  # Это переменная окружения, которая хранит токен бота

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

@bot.command()
async def admin(ctx):
    await ctx.send("Admin roles: " + ", ".join(admin_roles))

@bot.command()
async def autoplay(ctx):
    global autoplay
    autoplay = not autoplay
    await ctx.send(f"Autoplay is now {'enabled' if autoplay else 'disabled'}.")

@bot.command()
async def clear(ctx):
    queue.clear()
    await ctx.send("🗑️ Queue cleared.")

@bot.command()
async def disconnect(ctx):
    queue.clear()
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Disconnected and cleared queue.")

@bot.command()
async def discover(ctx, *, tag=None):
    await ctx.send(f"🔍 Discovering music by tag: #{tag if tag else 'none'} (not implemented yet)")

@bot.command()
async def feed(ctx):
    await ctx.send("📰 Fetching your repost feed... (not implemented yet)")

# Переименовали команду help в custom_help
@bot.command(name="custom_help")
async def custom_help(ctx):
    commands_list = [cmd.name for cmd in bot.commands]
    await ctx.send("📚 Available commands: " + ", ".join(commands_list))

@bot.command()
async def likes(ctx):
    await ctx.send("💖 Playing your liked tracks... (not implemented yet)")

@bot.command()
async def loop(ctx, mode=None):
    global loop_mode
    if mode in ["off", "queue", "track"]:
        loop_mode = mode
    await ctx.send(f"🔁 Loop mode is: {loop_mode}")

@bot.command()
async def next_up(ctx, *, url):
    queue.appendleft(url)
    await ctx.send("🎯 Added to top of queue.")

@bot.command()
async def now_playing(ctx):
    if now_playing:
        embed = discord.Embed(title="🎵 Now Playing", description=now_playing['title'], color=discord.Color.orange())
        embed.add_field(name="Link", value=now_playing.get('webpage_url'), inline=False)
        embed.set_thumbnail(url=now_playing.get('thumbnail', discord.Embed.Empty))
        await ctx.send(embed=embed)
    else:
        await ctx.send("🚫 Nothing is playing.")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused.")

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)} ms")

@bot.command()
async def play(ctx, *, search):
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    queue.append(search)
    await ctx.send("🎶 Added to queue.")

    if not ctx.voice_client.is_playing():
        await play_next(ctx)

@bot.command()
async def playlists(ctx):
    await ctx.send("📂 Your playlists (not implemented yet)")

@bot.command(name="queue")
async def queue_list(ctx):
    if queue:
        msg = "\n".join([f"{i+1}. {url}" for i, url in enumerate(queue)])
        embed = discord.Embed(title="🎵 Queue", description=msg, color=discord.Color.blue())
        await ctx.send(embed=embed)
    else:
        await ctx.send("🕳️ Queue is empty.")

@bot.command()
async def remove(ctx, index: int):
    try:
        removed = queue[index - 1]
        del queue[index - 1]
        await ctx.send(f"🗑️ Removed: {removed}")
    except:
        await ctx.send("❌ Invalid track number.")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed.")

@bot.command()
async def search(ctx, *, term):
    await play(ctx, search=term)

@bot.command()
async def seek(ctx, seconds: int):
    await ctx.send("⏩ Seek is not implemented in this version.")

@bot.command()
async def shuffle(ctx):
    import random
    random.shuffle(queue)
    await ctx.send("🔀 Queue shuffled.")

@bot.command()
async def shut_up(ctx):
    await ctx.invoke(bot.get_command("stop"))

@bot.command()
async def sign_in(ctx):
    await ctx.send("🔐 Sign in (not implemented)")

@bot.command()
async def sign_out(ctx):
    await ctx.send("🚪 Signed out (not implemented)")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped.")

@bot.command()
async def stop(ctx):
    queue.clear()
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⛔ Stopped and cleared queue.")

@bot.command()
async def volume(ctx, value: int = None):
    global volume
    if value is not None:
        volume = min(max(value / 100, 0), 2.0)
    await ctx.send(f"🔊 Volume is set to: {int(volume * 100)}%")

# Используем токен из переменной окружения
bot.run(TOKEN)
