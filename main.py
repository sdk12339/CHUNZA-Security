import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import os
import sys
import json
import yt_dlp
import random
import time
from threading import Thread
from flask import Flask

# --- [1] 기본 정보 및 컬러 설정 ---
VERSION = "v2.0.0"
AUTHOR = "CHUNZA"
CYAN, RED, GREEN, YELLOW, RESET, BOLD = "\033[96m", "\033[91m", "\033[92m", "\033[93m", "\033[0m", "\033[1m"
DATA_FILE = "server_data.json"

# --- [2] 데이터 및 음악 설정 ---
db = {
    "admins": [681815009466253416],
    "master_id": 731129858629042187,
    "settings": {"verify_role_name": "시민", "verify_emoji": "✅"},
    "channels": {
        "vote": 1501240737352646728, 
        "suggestion": 1501199686932103199, 
        "verify": 1501199548880650331,
        "music": None,
        "music_msg": None
    },
    "active_votes": {},
    "vote_logs": {}
}

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'quiet': True, 'no_warnings': True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

# 음악 상태 관리
music_state = {
    "queue": [], 
    "loop": False, 
    "current": None, 
    "start_time": 0, 
    "duration": 0
}

def load_data():
    global db
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                db.update(json.load(f))
        except: pass

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{CYAN}{BOLD}\n    ██████╗██╗  ██╗██╗   ██╗███╗   ██╗███████╗ █████╗ \n   ██╔════╝██║  ██║██║   ██║████╗  ██║╚══███╔╝██╔══██╗\n   ██║     ███████║██║   ██║██╔██╗ ██║  ███╔╝ ███████║\n   ██║     ██╔══██║██║   ██║██║╚██╗██║ ███╔╝  ██╔══██║\n   ╚██████╗██║  ██║╚██████╔╝██║ ╚████║███████╗██║  ██║\n    ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝{RESET}")
    print(f"          {YELLOW}>> PRECISION CONTROL | {VERSION} <<{RESET}")

# --- [3] 봇 클래스 설정 ---
print_banner()
TOKEN = input(f"{CYAN}[>] INPUT BOT TOKEN: {RESET}").strip()
GUILD_ID = int(input(f"{CYAN}[>] INPUT TARGET SERVER ID: {RESET}").strip())

class ChunzaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = ChunzaBot()

def is_auth(interaction: discord.Interaction):
    return interaction.user.id == db["master_id"] or interaction.user.id in db["admins"]

# --- [4] 유틸리티 기능 ---

def format_time(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))

async def update_music_embed(guild, status_text="대기 중..."):
    ch = bot.get_channel(db["channels"]["music"])
    if not ch: return
    
    color = 0x00ff00 if music_state["current"] else 0x5865f2
    embed = discord.Embed(title="🎶 CHUNZA MUSIC SYSTEM", description=status_text, color=color)
    
    if music_state["current"]:
        elapsed = time.time() - music_state["start_time"]
        progress = f"⏳ {format_time(elapsed)} / {format_time(music_state['duration'])}"
        embed.add_field(name="진행 시간", value=progress, inline=False)
    
    q_list = "\n".join([f"• {s['title']}" for s in music_state["queue"][:5]]) or "비어 있음"
    embed.add_field(name="대기열 (최근 5곡)", value=q_list, inline=False)
    embed.set_footer(text=f"반복: {'ON' if music_state['loop'] else 'OFF'} | 채팅으로 노래 검색")

    try:
        msg = await ch.fetch_message(db["channels"]["music_msg"])
        await msg.edit(embed=embed)
    except:
        msg = await ch.send(embed=embed)
        db["channels"]["music_msg"] = msg.id
        save_data()
        for emoji in ["⏹️", "🔁", "🔀", "⏭️", "⏯️"]:
            await msg.add_reaction(emoji)

async def play_next(guild):
    vc = guild.voice_client
    if not vc: return

    if not music_state["queue"]:
        music_state["current"] = None
        await update_music_embed(guild, "⏹️ 모든 곡 재생 완료")
        return

    song = music_state["queue"].pop(0)
    music_state["current"] = song
    music_state["start_time"] = time.time()
    music_state["duration"] = song["duration"]

    def after_playing(error):
        if music_state["loop"] and music_state["current"]:
            music_state["queue"].insert(0, music_state["current"])
        asyncio.run_coroutine_threadsafe(play_next(guild), bot.loop)

    vc.play(discord.FFmpegPCMAudio(song['url'], **FFMPEG_OPTIONS), after=after_playing)
    await update_music_embed(guild, f"🎵 재생 중: **{song['title']}**")

# --- [5] 이벤트 핸들러 ---

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    if message.channel.id == db["channels"].get("music"):
        await message.delete()
        if not message.author.voice:
            return await message.channel.send("⚠️ 음성 채널에 먼저 접속하세요.", delete_after=3)
        
        vc = message.guild.voice_client or await message.author.voice.channel.connect()
        
        async with message.channel.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{message.content}", download=False)['entries'][0]
                music_state["queue"].append({
                    "url": info['url'], 
                    "title": info['title'], 
                    "duration": info.get('duration', 0)
                })
        
        if not vc.is_playing():
            await play_next(message.guild)
        else:
            await update_music_embed(message.guild, f"➕ 추가됨: {info['title']}")

    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member: member = await guild.fetch_member(payload.user_id)

    # [입국 심사 - 역할 부여]
    if payload.channel_id == db["channels"]["verify"]:
        if str(payload.emoji) == db["settings"]["verify_emoji"]:
            role = discord.utils.get(guild.roles, name=db["settings"]["verify_role_name"])
            if role: await member.add_roles(role)
        return

    # [음악 컨트롤]
    if payload.channel_id == db["channels"]["music"] and payload.message_id == db["channels"]["music_msg"]:
        vc = guild.voice_client
        msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        await msg.remove_reaction(payload.emoji, member)
        if not vc: return

        emoji = str(payload.emoji)
        if emoji == "⏹️": 
            music_state["queue"] = []; music_state["current"] = None
            await vc.disconnect(); await update_music_embed(guild, "⏹️ 정지됨")
        elif emoji == "🔁":
            music_state["loop"] = not music_state["loop"]
            await update_music_embed(guild)
        elif emoji == "🔀":
            random.shuffle(music_state["queue"]); await update_music_embed(guild, "🔀 셔플 완료")
        elif emoji == "⏭️":
            vc.stop()
        elif emoji == "⏯️":
            if vc.is_paused(): vc.resume()
            else: vc.pause()
            await update_music_embed(guild)
        return

    # [투표 시스템]
    vote_id = str(payload.message_id)
    if vote_id in db["active_votes"]:
        if str(payload.emoji) in ["⭕", "❌"]:
            if vote_id not in db["vote_logs"]: db["vote_logs"][vote_id] = []
            if payload.user_id in db["vote_logs"][vote_id]:
                msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                await msg.remove_reaction(payload.emoji, member)
            else:
                db["vote_logs"][vote_id].append(payload.user_id)
                save_data()
                master = await bot.fetch_user(db["master_id"])
                await master.send(f"🗳️ [투표] {member} -> {payload.emoji} ({db['active_votes'][vote_id]['topic']})")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id: return
    guild = bot.get_guild(payload.guild_id)
    member = await guild.fetch_member(payload.user_id)

    # [입국 심사 - 역할 제거]
    if payload.channel_id == db["channels"]["verify"]:
        if str(payload.emoji) == db["settings"]["verify_emoji"]:
            role = discord.utils.get(guild.roles, name=db["settings"]["verify_role_name"])
            if role: await member.remove_roles(role)

# --- [6] 슬래시 명령어 ---

@bot.tree.command(name="음악", description="음악 전용 채널 설정")
async def music_setup(interaction: discord.Interaction, 채널: discord.TextChannel):
    if not is_auth(interaction): return
    db["channels"]["music"] = 채널.id
    db["channels"]["music_msg"] = None
    save_data()
    await update_music_embed(interaction.guild)
    await interaction.response.send_message(f"✅ {채널.mention}을 음악 채널로 설정했습니다.")

@bot.tree.command(name="잠금", description="채팅 권한 잠금 (메시지/스레드)")
async def lock_slash(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    role = discord.utils.get(interaction.guild.roles, name=db["settings"]["verify_role_name"])
    overwrites = target.overwrites_for(role)
    overwrites.send_messages = False
    overwrites.send_messages_in_threads = False
    overwrites.create_public_threads = False
    overwrites.create_private_threads = False
    await target.set_permissions(role, overwrite=overwrites)
    await interaction.response.send_message(f"🔒 {target.mention} 잠금.")

@bot.tree.command(name="해제", description="채팅 권한 해제")
async def unlock_slash(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    role = discord.utils.get(interaction.guild.roles, name=db["settings"]["verify_role_name"])
    overwrites = target.overwrites_for(role)
    overwrites.send_messages = True
    await target.set_permissions(role, overwrite=overwrites)
    await interaction.response.send_message(f"🔓 {target.mention} 해제.")

@bot.tree.command(name="투표", description="중복 금지 투표 시작")
async def vote_slash(interaction: discord.Interaction, 주제: str):
    if interaction.channel_id != db["channels"]["vote"]: return await interaction.response.send_message("투표 채널에서 사용하세요.")
    embed = discord.Embed(title="🗳️ 익명 투표", description=f"**{주제}**", color=0xf1c40f)
    await interaction.response.send_message("투표 시작", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("⭕"); await msg.add_reaction("❌")
    db["active_votes"][str(msg.id)] = {"topic": 주제, "channel": interaction.channel_id}
    save_data()

@bot.tree.command(name="청소", description="메시지 삭제")
async def clear_slash(interaction: discord.Interaction, 수량: int):
    if not is_auth(interaction): return
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=수량)
    await interaction.followup.send(f"🧹 {수량}개 삭제 완료.")

@bot.tree.command(name="권한부여", description="관리자 등록")
async def auth_add(interaction: discord.Interaction, 유저: discord.Member):
    if interaction.user.id != db["master_id"]: return
    if 유저.id not in db["admins"]: db["admins"].append(유저.id); save_data()
    await interaction.response.send_message(f"✅ {유저.mention} 관리자 등록.")

@bot.tree.command(name="권한해제", description="관리자 해제")
async def auth_remove(interaction: discord.Interaction, 유저: discord.Member):
    if interaction.user.id != db["master_id"]: return
    if 유저.id in db["admins"]: db["admins"].remove(유저.id); save_data()
    await interaction.response.send_message(f"❌ {유저.mention} 권한 해제.")

@bot.tree.command(name="명령어", description="도움말")
async def help_slash(interaction: discord.Interaction):
    embed = discord.Embed(title=f"🛡️ {AUTHOR} {VERSION}", color=0x3498db)
    embed.add_field(name="음악", value="`/음악` 설정 후 채팅 입력", inline=True)
    embed.add_field(name="관리", value="`/잠금`, `/해제`, `/청소`, `/권한부여`", inline=False)
    await interaction.response.send_message(embed=embed)

# --- [7] 루프 및 서버 실행 ---

async def status_task():
    while True:
        for guild in bot.guilds:
            if guild.voice_client and guild.voice_client.is_playing():
                await update_music_embed(guild, f"🎵 재생 중: **{music_state['current']['title']}**")
        await asyncio.sleep(10) # 10초마다 재생 시간 업데이트

@bot.event
async def on_ready():
    load_data(); print_banner()
    bot.loop.create_task(status_task())
    print(f"{GREEN}[+] CHUNZA ONLINE: {bot.user}{RESET}")

app = Flask('')
@app.route('/')
def home(): return "CHUNZA v2.0.0 Online"
def run_app(): app.run(host='0.0.0.0', port=8080)
Thread(target=run_app, daemon=True).start()

if __name__ == "__main__":
    bot.run(TOKEN)
