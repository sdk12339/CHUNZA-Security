import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import os
import sys
import json
import yt_dlp
from threading import Thread
from flask import Flask

# --- [1] 기본 정보 및 컬러 설정 ---
VERSION = "v1.7.0"
AUTHOR = "CHUNZA"
CYAN, RED, GREEN, YELLOW, RESET, BOLD = "\033[96m", "\033[91m", "\033[92m", "\033[93m", "\033[0m", "\033[1m"
DATA_FILE = "server_data.json"

# --- [2] 데이터 및 음악 설정 ---
db = {
    "admins": [681815009466253416],
    "master_id": 731129858629042187,
    "settings": {"verify_role_name": "시민", "verify_emoji": "✅"},
    "channels": {"vote": 1501240737352646728, "suggestion": 1501199686932103199, "verify": 1501199548880650331},
}

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'quiet': True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

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
    print(f"          {YELLOW}>> SLASH COMMANDS & MUSIC | {VERSION} <<{RESET}")

# --- [3] 봇 클래스 설정 ---
print_banner()
TOKEN = input(f"{CYAN}[>] INPUT BOT TOKEN: {RESET}").strip()
GUILD_ID = int(input(f"{CYAN}[>] INPUT TARGET SERVER ID: {RESET}").strip())

class ChunzaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        # 슬래시 명령어를 지정된 서버에 즉시 동기화
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = ChunzaBot()

def is_auth(interaction: discord.Interaction):
    return interaction.user.id == db["master_id"] or interaction.user.id in db["admins"]

# --- [4] 입국 심사 시스템 ---
@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != db["channels"]["verify"]: return
    if str(payload.emoji) != db["settings"]["verify_emoji"]: return
    guild = bot.get_guild(payload.guild_id)
    role = discord.utils.get(guild.roles, name=db["settings"]["verify_role_name"])
    if role: await payload.member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != db["channels"]["verify"]: return
    if str(payload.emoji) != db["settings"]["verify_emoji"]: return
    guild = bot.get_guild(payload.guild_id)
    member = await guild.fetch_member(payload.user_id)
    role = discord.utils.get(guild.roles, name=db["settings"]["verify_role_name"])
    if role: await member.remove_roles(role)

# --- [5] 음악 기능 (Music Commands) ---
@bot.tree.command(name="재생", description="유튜브 노래를 재생합니다.")
async def play(interaction: discord.Interaction, 검색어: str):
    if not interaction.user.voice:
        return await interaction.response.send_message("🔊 음성 채널에 먼저 입장하세요!", ephemeral=True)

    await interaction.response.defer()
    channel = interaction.user.voice.channel

    vc = interaction.guild.voice_client
    if not vc: vc = await channel.connect()

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{검색어}", download=False)['entries'][0]
        url = info['url']
        title = info['title']

    if vc.is_playing(): vc.stop()
    vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
    await interaction.followup.send(f"🎵 **재생 중:** {title}")

@bot.tree.command(name="정지", description="음악을 정지하고 채널에서 나갑니다.")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("⏹️ 음악을 정지했습니다.")
    else:
        await interaction.response.send_message("재생 중인 음악이 없습니다.", ephemeral=True)

# --- [6] 관리 및 보안 기능 (Slash) ---
@bot.tree.command(name="명령어", description="모든 명령어 목록을 확인합니다.")
async def help_slash(interaction: discord.Interaction):
    embed = discord.Embed(title="🛡️ CHUNZA SYSTEM", color=0x3498db)
    embed.add_field(name="🎶 음악", value="`/재생`, `/정지`", inline=False)
    embed.add_field(name="🌐 일반", value="`/현황`, `/문의`, `/투표`", inline=False)
    embed.add_field(name="🛡️ 관리", value="`/청소`, `/추방`, `/차단`, `/잠금`, `/해제`, `/백업`", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="청소", description="메시지를 삭제합니다.")
@app_commands.describe(수량="삭제할 메시지 수")
async def clear_slash(interaction: discord.Interaction, 수량: int):
    if not is_auth(interaction): return await interaction.response.send_message("권한 부족.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=수량)
    await interaction.followup.send(f"🧹 {len(deleted)}개의 메시지를 청소했습니다.")

@bot.tree.command(name="현황", description="서버 인원 현황을 확인합니다.")
async def status_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"📊 현재 서버 인원: **{interaction.guild.member_count}명**")

@bot.tree.command(name="투표", description="익명 투표를 시작합니다.")
async def vote_slash(interaction: discord.Interaction, 주제: str):
    if interaction.channel_id != db["channels"]["vote"]:
        return await interaction.response.send_message("투표 채널이 아닙니다.", ephemeral=True)

    embed = discord.Embed(title="🗳️ 익명 투표", description=f"**주제: {주제}**", color=0xf1c40f)
    await interaction.response.send_message("투표를 시작합니다.", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("⭕")
    await msg.add_reaction("❌")

@bot.tree.command(name="권한부여", description="관리자를 추가합니다. (마스터 전용)")
async def auth_add(interaction: discord.Interaction, 유저: discord.Member):
    if interaction.user.id != db["master_id"]: return
    if 유저.id not in db["admins"]:
        db["admins"].append(유저.id); save_data()
        await interaction.response.send_message(f"✅ {유저.mention} 님을 관리자로 등록했습니다.")

@bot.tree.command(name="백업", description="현재 설정을 저장합니다.")
async def backup_slash(interaction: discord.Interaction):
    if not is_auth(interaction): return
    save_data()
    await interaction.response.send_message("💾 데이터 백업이 완료되었습니다.")

# --- [7] 서버 실행 및 초기화 ---
@bot.event
async def on_ready():
    load_data()
    print_banner()
    print(f"{GREEN}[+] CHUNZA {VERSION} ONLINE: {bot.user}{RESET}")

app = Flask('')
@app.route('/')
def home(): return "CHUNZA v1.7.0 Online"
def run_app(): app.run(host='0.0.0.0', port=8080)
Thread(target=run_app, daemon=True).start()

if __name__ == "__main__":
    bot.run(TOKEN)
