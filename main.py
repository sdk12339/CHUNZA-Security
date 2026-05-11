import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import os
import json
import yt_dlp
import random
import time
from threading import Thread
from flask import Flask

# --- [1] 기본 정보 및 컬러 설정 ---
VERSION = "v2.2.0"
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

# --- [4] 음악 유틸리티 ---

async def update_music_embed(guild, status_text="대기 중..."):
    ch = bot.get_channel(db["channels"]["music"])
    if not ch: return
    
    color = 0x00ff00 if music_state["current"] else 0x5865f2
    embed = discord.Embed(title="🎶 CHUNZA MUSIC SYSTEM", description=status_text, color=color)
    
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

    def after_playing(error):
        if music_state["loop"] and music_state["current"]:
            music_state["queue"].insert(0, music_state["current"])
        music_state["current"] = None 
        asyncio.run_coroutine_threadsafe(play_next(guild), bot.loop)

    try:
        vc.play(discord.FFmpegPCMAudio(song['url'], **FFMPEG_OPTIONS), after=after_playing)
        await update_music_embed(guild, f"🎵 재생 중: **{song['title']}**")
    except:
        await play_next(guild)

# --- [5] 이벤트 핸들러 ---

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    if message.channel.id == db["channels"].get("music"):
        await message.delete()
        if not message.author.voice:
            return await message.channel.send("⚠️ 음성 채널에 접속하세요.", delete_after=3)
        
        vc = message.guild.voice_client or await message.author.voice.channel.connect()
        
        async with message.channel.typing():
            try:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(f"ytsearch:{message.content}", download=False)['entries'][0]
                    music_state["queue"].append({"url": info['url'], "title": info['title']})
            except:
                return await message.channel.send("❌ 검색 결과가 없습니다.", delete_after=3)
        
        if not vc.is_playing():
            await play_next(message.guild)
        else:
            await update_music_embed(message.guild, f"➕ 추가됨: {info['title']}")

    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)

    if payload.channel_id == db["channels"]["verify"]:
        if str(payload.emoji) == db["settings"]["verify_emoji"]:
            role = discord.utils.get(guild.roles, name=db["settings"]["verify_role_name"])
            if role: await member.add_roles(role)
        return

    if payload.channel_id == db["channels"]["music"] and payload.message_id == db["channels"]["music_msg"]:
        vc = guild.voice_client
        msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        await msg.remove_reaction(payload.emoji, member)
        if not vc: return
        emoji = str(payload.emoji)
        if emoji == "⏹️": 
            music_state["queue"] = []; music_state["current"] = None
            if vc.is_playing(): vc.stop()
            await vc.disconnect(); await update_music_embed(guild, "⏹️ 정지됨")
        elif emoji == "🔁":
            music_state["loop"] = not music_state["loop"]; await update_music_embed(guild)
        elif emoji == "🔀":
            random.shuffle(music_state["queue"]); await update_music_embed(guild, "🔀 셔플 완료")
        elif emoji == "⏭️":
            if vc.is_playing(): vc.stop()
        elif emoji == "⏯️":
            if vc.is_paused(): vc.resume()
            else: vc.pause()
            await update_music_embed(guild)
        return

    vote_id = str(payload.message_id)
    if vote_id in db["active_votes"]:
        if str(payload.emoji) in ["⭕", "❌"]:
            if vote_id not in db["vote_logs"]: db["vote_logs"][vote_id] = []
            if payload.user_id in db["vote_logs"][vote_id]:
                msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                await msg.remove_reaction(payload.emoji, member)
            else:
                db["vote_logs"][vote_id].append(payload.user_id); save_data()
                master = await bot.fetch_user(db["master_id"])
                await master.send(f"🗳️ [투표] {member} -> {payload.emoji} ({db['active_votes'][vote_id]['topic']})")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id: return
    guild = bot.get_guild(payload.guild_id)
    member = await guild.fetch_member(payload.user_id)
    if payload.channel_id == db["channels"]["verify"]:
        if str(payload.emoji) == db["settings"]["verify_emoji"]:
            role = discord.utils.get(guild.roles, name=db["settings"]["verify_role_name"])
            if role: await member.remove_roles(role)

# --- [6] 슬래시 명령어 ---

@bot.tree.command(name="삭제", description="메시지를 삭제합니다.")
@app_commands.describe(수량="삭제할 메시지 개수", 채널="삭제할 채널(미지정 시 현재 채널)")
async def delete_slash(interaction: discord.Interaction, 수량: int, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    await interaction.response.defer(ephemeral=True)
    deleted = await target.purge(limit=수량)
    await interaction.followup.send(f"🧹 {target.mention}에서 {len(deleted)}개의 메시지를 삭제했습니다.")

@bot.tree.command(name="음악", description="음악 전용 채널 설정")
async def music_setup(interaction: discord.Interaction, 채널: discord.TextChannel):
    if not is_auth(interaction): return
    db["channels"]["music"] = 채널.id
    db["channels"]["music_msg"] = None
    save_data()
    await interaction.response.send_message(f"✅ {채널.mention} 설정 완료.")
    await update_music_embed(interaction.guild)

@bot.tree.command(name="잠금", description="채팅 권한 잠금")
async def lock_slash(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    role = discord.utils.get(interaction.guild.roles, name=db["settings"]["verify_role_name"])
    overwrites = target.overwrites_for(role)
    overwrites.send_messages = False
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

@bot.tree.command(name="투표", description="투표 시작")
async def vote_slash(interaction: discord.Interaction, 주제: str):
    if interaction.channel_id != db["channels"]["vote"]: return await interaction.response.send_message("투표 채널에서 사용하세요.")
    embed = discord.Embed(title="🗳️ 익명 투표", description=f"**{주제}**", color=0xf1c40f)
    await interaction.response.send_message("투표 시작", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("⭕"); await msg.add_reaction("❌")
    db["active_votes"][str(msg.id)] = {"topic": 주제}
    save_data()

@bot.tree.command(name="권한부여", description="관리자 등록")
async def auth_add(interaction: discord.Interaction, 유저: discord.Member):
    if interaction.user.id != db["master_id"]: return
    if 유저.id not in db["admins"]: db["admins"].append(유저.id); save_data()
    await interaction.response.send_message(f"✅ {유저.mention} 등록.")

@bot.tree.command(name="명령어", description="도움말")
async def help_slash(interaction: discord.Interaction):
    embed = discord.Embed(title=f"🛡️ {AUTHOR} SYSTEM", color=0x3498db)
    embed.add_field(name="기능", value="`/삭제`, `/음악`, `/잠금`, `/해제`, `/투표`", inline=False)
    await interaction.response.send_message(embed=embed)

# --- [7] 실행 ---

@bot.event
async def on_ready():
    load_data(); print_banner()
    print(f"{GREEN}[+] ONLINE: {bot.user}{RESET}")

app = Flask('')
@app.route('/')
def home(): return "Online"
def run_app(): app.run(host='0.0.0.0', port=8080)
Thread(target=run_app, daemon=True).start()

if __name__ == "__main__":
    bot.run(TOKEN)
