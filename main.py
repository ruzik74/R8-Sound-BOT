import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque

# Установка намерений (intents)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Опции для yt-dlp
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'default_search': 'auto',
    'noplaylist': True,
    'extract_flat': False,
}

# Очередь воспроизведения
queue = deque()
autoplay = False
loop_mode = "off"  # "off", "track", "queue"
now_playing = None
volume = 0.5
admin_roles = ["Admin"]  # Роли администраторов

# Проверка на роль администратора
def is_admin():
    async def predicate(ctx):
        return any(role.name in admin_roles for role in ctx.author.roles)
    return commands.check(predicate)

# Событие, когда бот готов
@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')

# Обработка следующего трека
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

# Команды бота
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
async def play(ctx, *, search):
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    queue.append(search)
    await ctx.send("🎶 Added to queue.")

    if not ctx.voice_client.is_playing():
        await play_next(ctx)

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

# Запуск бота
if __name__ == '__main__':
    bot.run('YOUR_BOT_TOKEN')  # Замените на свой токен бота
