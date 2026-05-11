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
VERSION = "v1.8.0"
AUTHOR = "CHUNZA"
CYAN, RED, GREEN, YELLOW, RESET, BOLD = "\033[96m", "\033[91m", "\033[92m", "\033[93m", "\033[0m", "\033[1m"
DATA_FILE = "server_data.json"

# --- [2] 데이터 및 음악 설정 ---
db = {
    "admins": [681815009466253416],
    "master_id": 731129858629042187,
    "settings": {"verify_role_name": "시민", "verify_emoji": "✅"},
    "channels": {"vote": 1501240737352646728, "suggestion": 1501199686932103199, "verify": 1501199548880650331},
    "active_votes": {}
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

# --- [4] 입국 심사 (Reaction) ---
@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != db["channels"]["verify"]: return
    if str(payload.emoji) != db["settings"]["verify_emoji"]: return
    guild = bot.get_guild(payload.guild_id)
    role = discord.utils.get(guild.roles, name=db["settings"]["verify_role_name"])
    if role: 
        member = guild.get_member(payload.user_id)
        if member: await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != db["channels"]["verify"]: return
    if str(payload.emoji) != db["settings"]["verify_emoji"]: return
    guild = bot.get_guild(payload.guild_id)
    member = await guild.fetch_member(payload.user_id)
    role = discord.utils.get(guild.roles, name=db["settings"]["verify_role_name"])
    if role: await member.remove_roles(role)

# --- [5] 음악 기능 ---
@bot.tree.command(name="재생", description="유튜브 음악을 재생합니다.")
async def play(interaction: discord.Interaction, 검색어: str):
    if not interaction.user.voice: return await interaction.response.send_message("🔊 음성 채널에 입장하세요!", ephemeral=True)
    await interaction.response.defer()
    vc = interaction.guild.voice_client or await interaction.user.voice.channel.connect()
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{검색어}", download=False)['entries'][0]
        url, title = info['url'], info['title']
    if vc.is_playing(): vc.stop()
    vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
    await interaction.followup.send(f"🎵 **재생 중:** {title}")

@bot.tree.command(name="정지", description="음악을 정지합니다.")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc: await vc.disconnect(); await interaction.response.send_message("⏹️ 정지되었습니다.")
    else: await interaction.response.send_message("재생 중이 아닙니다.", ephemeral=True)

# --- [6] 보안 및 관리 기능 (요청 사항 수정 반영) ---

@bot.tree.command(name="권한부여", description="새로운 관리자를 등록합니다.")
async def auth_add(interaction: discord.Interaction, 유저: discord.Member):
    if interaction.user.id != db["master_id"]: return await interaction.response.send_message("마스터 전용 권한입니다.", ephemeral=True)
    if 유저.id not in db["admins"]:
        db["admins"].append(유저.id); save_data()
        await interaction.response.send_message(f"✅ {유저.mention} 님이 관리자로 등록되었습니다.")
    else: await interaction.response.send_message("이미 관리자입니다.", ephemeral=True)

@bot.tree.command(name="권한해제", description="관리자 권한을 회수합니다.")
async def auth_remove(interaction: discord.Interaction, 유저: discord.Member):
    if interaction.user.id != db["master_id"]: return await interaction.response.send_message("마스터 전용 권한입니다.", ephemeral=True)
    if 유저.id in db["admins"]:
        db["admins"].remove(유저.id); save_data()
        await interaction.response.send_message(f"❌ {유저.mention} 님의 권한이 해제되었습니다.")
    else: await interaction.response.send_message("등록된 관리자가 아닙니다.", ephemeral=True)

@bot.tree.command(name="잠금", description="시민 역할의 채팅 및 스레드 권한을 차단합니다.")
async def lock_slash(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    role = discord.utils.get(interaction.guild.roles, name=db["settings"]["verify_role_name"])
    if not role: return await interaction.response.send_message(f"'{db['settings']['verify_role_name']}' 역할을 찾을 수 없습니다.", ephemeral=True)

    # 요청하신 4가지 권한만 차단 (나머지는 건들지 않음)
    overwrites = target.overwrites_for(role)
    overwrites.send_messages = False
    overwrites.send_messages_in_threads = False
    overwrites.create_public_threads = False
    overwrites.create_private_threads = False

    await target.set_permissions(role, overwrite=overwrites)
    await interaction.response.send_message(f"🔒 {target.mention} 채널의 시민 권한(메시지/스레드)이 잠겼습니다.")

@bot.tree.command(name="해제", description="시민 역할의 모든 제한을 해제하고 메시지 권한을 켭니다.")
async def unlock_slash(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    role = discord.utils.get(interaction.guild.roles, name=db["settings"]["verify_role_name"])
    if not role: return await interaction.response.send_message(f"'{db['settings']['verify_role_name']}' 역할을 찾을 수 없습니다.", ephemeral=True)

    # 모든 권한을 다시 중립(None) 또는 허용(True)으로 변경
    overwrites = target.overwrites_for(role)
    overwrites.send_messages = True
    overwrites.send_messages_in_threads = None
    overwrites.create_public_threads = None
    overwrites.create_private_threads = None

    await target.set_permissions(role, overwrite=overwrites)
    await interaction.response.send_message(f"🔓 {target.mention} 채널의 시민 권한이 정상화되었습니다.")

@bot.tree.command(name="문의", description="개발자 건의사항 전송")
async def contact_slash(interaction: discord.Interaction, 내용: str):
    if interaction.channel_id != db["channels"]["suggestion"]: return await interaction.response.send_message("건의 채널에서 사용하세요.", ephemeral=True)
    master = await bot.fetch_user(db["master_id"])
    await master.send(f"📩 [{interaction.user}] 문의: {내용}")
    await interaction.response.send_message("✅ 건의가 전달되었습니다.", ephemeral=True)

@bot.tree.command(name="생성", description="채널 생성")
async def create_slash(interaction: discord.Interaction, 카테고리id: str, 이름: str):
    if not is_auth(interaction): return
    cat = bot.get_channel(int(카테고리id))
    new_ch = await interaction.guild.create_text_channel(이름, category=cat)
    await interaction.response.send_message(f"📂 {new_ch.mention} 생성 완료.")

@bot.tree.command(name="추방", description="추방")
async def kick_slash(interaction: discord.Interaction, 유저: discord.Member):
    if not is_auth(interaction): return
    await 유저.kick(); await interaction.response.send_message(f"👢 {유저.display_name} 추방.")

@bot.tree.command(name="차단", description="차단")
async def ban_slash(interaction: discord.Interaction, 유저: discord.Member):
    if not is_auth(interaction): return
    await 유저.ban(); await interaction.response.send_message(f"🔨 {유저.display_name} 차단.")

@bot.tree.command(name="삭제", description="채널 삭제")
async def delete_slash(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    await target.delete(); await interaction.response.send_message("삭제 완료.", ephemeral=True)

@bot.tree.command(name="복구", description="데이터 복구")
async def restore_slash(interaction: discord.Interaction):
    if not is_auth(interaction): return
    load_data(); await interaction.response.send_message("🛠️ 데이터 복구 완료.")

@bot.tree.command(name="투표", description="익명 투표 시작")
async def vote_slash(interaction: discord.Interaction, 주제: str):
    if interaction.channel_id != db["channels"]["vote"]: return await interaction.response.send_message("투표 채널 전용입니다.", ephemeral=True)
    embed = discord.Embed(title="🗳️ 익명 투표", description=f"**{주제}**", color=0xf1c40f)
    await interaction.response.send_message("시작", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("⭕"); await msg.add_reaction("❌")
    db["active_votes"][str(msg.id)] = {"topic": 주제, "channel": interaction.channel_id}

@bot.tree.command(name="결과", description="마지막 투표 종료")
async def result_slash(interaction: discord.Interaction):
    if not db["active_votes"]: return await interaction.response.send_message("투표 없음.", ephemeral=True)
    msg_id = list(db["active_votes"].keys())[-1]
    data = db["active_votes"].pop(msg_id)
    ch = bot.get_channel(data["channel"])
    msg = await ch.fetch_message(int(msg_id))
    results = {str(r.emoji): r.count - 1 for r in msg.reactions if str(r.emoji) in ["⭕", "❌"]}
    await interaction.response.send_message(f"🏁 **결과**\n주제: {data['topic']}\n⭕: {results.get('⭕',0)} | ❌: {results.get('❌',0)}")
    await msg.delete()

@bot.tree.command(name="명령어", description="명령어 목록")
async def help_slash(interaction: discord.Interaction):
    embed = discord.Embed(title=f"🛡️ {AUTHOR} {VERSION}", color=0x3498db)
    embed.add_field(name="🎶 Music", value="`/재생`, `/정지`", inline=True)
    embed.add_field(name="🛡️ Admin", value="`/청소`, `/추방`, `/차단`, `/잠금`, `/해제`, `/생성`, `/삭제`, `/권한부여`, `/권한해제`, `/백업`, `/복구`", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="청소", description="청소")
async def clear_slash(interaction: discord.Interaction, 수량: int):
    if not is_auth(interaction): return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=수량)
    await interaction.followup.send(f"🧹 {len(deleted)}개 삭제.")

@bot.tree.command(name="현황", description="서버 인원")
async def status_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"📊 인원: **{interaction.guild.member_count}명**")

@bot.tree.command(name="백업", description="데이터 백업")
async def backup_slash(interaction: discord.Interaction):
    if not is_auth(interaction): return
    save_data(); await interaction.response.send_message("💾 백업 완료.")

# --- [7] 서버 실행 ---
@bot.event
async def on_ready():
    load_data(); print_banner()
    print(f"{GREEN}[+] CHUNZA {VERSION} ONLINE: {bot.user}{RESET}")

app = Flask('')
@app.route('/')
def home(): return "CHUNZA v1.8.0 Online"
def run_app(): app.run(host='0.0.0.0', port=8080)
Thread(target=run_app, daemon=True).start()

if __name__ == "__main__":
    bot.run(TOKEN)
