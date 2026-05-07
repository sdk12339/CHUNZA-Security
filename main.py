import discord
from discord.ext import commands
import datetime
import asyncio
import os
import sys
import json
from threading import Thread
from flask import Flask

# --- [1] 기본 정보 및 컬러 설정 ---
VERSION = "v1.5.0"
AUTHOR = "CHUNZA"
CYAN, RED, GREEN, YELLOW, RESET, BOLD = "\033[96m", "\033[91m", "\033[92m", "\033[93m", "\033[0m", "\033[1m"
DATA_FILE = "server_data.json"

# --- [2] 데이터 관리 시스템 (설정 및 데이터 저장 필수) ---
db = {
    "admins": [681815009466253416], # 기본 관리자 ID
    "master_id": 731129858629042187, # 개발자(Master) ID
    "channels": {
        "vote": 1501240737352646728,
        "suggestion": 1501199686932103199,
        "verify": 1501199548880650331
    },
    "active_votes": {}
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

# --- [3] UI 및 시스템 함수 ---
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    clear_screen()
    banner = f"""
{CYAN}{BOLD}
    ██████╗██╗  ██╗██╗   ██╗███╗   ██╗███████╗ █████╗ 
   ██╔════╝██║  ██║██║   ██║████╗  ██║╚══███╔╝██╔══██╗
   ██║     ███████║██║   ██║██╔██╗ ██║  ███╔╝ ███████║
   ██║     ██╔══██║██║   ██║██║╚██╗██║ ███╔╝  ██╔══██║
   ╚██████╗██║  ██║╚██████╔╝██║ ╚████║███████╗██║  ██║
    ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
{RESET}
          {YELLOW}>> SYSTEM INTEGRATED | VERSION: {VERSION} <<{RESET}
          {YELLOW}>>        CHUNZA MULTI-TOOL READY         <<{RESET}
    """
    print(banner)

# --- [4] 봇 초기 설정 및 입력 ---
print_banner()
TOKEN = input(f"{CYAN}[>] INPUT BOT TOKEN: {RESET}").strip()
GUILD_INPUT = input(f"{CYAN}[>] INPUT TARGET SERVER ID: {RESET}").strip()

try:
    TARGET_GUILD_ID = int(GUILD_INPUT)
except:
    print(f"{RED}[!] FATAL: INVALID SERVER ID.{RESET}")
    sys.exit()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# 권한 체크 함수
def is_auth(user):
    return user.id == db["master_id"] or user.id in db["admins"]

# --- [5] 메인 이벤트 (보안 및 관리) ---
@bot.event
async def on_ready():
    load_data()
    print_banner()
    print(f"{GREEN}[+] CHUNZA ONLINE: {bot.user}{RESET}")
    print(f"{GREEN}[+] MONITORING ID: {TARGET_GUILD_ID}{RESET}")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    if message.guild.id != TARGET_GUILD_ID: return

    # 투표 채널 관리 (명령어 외 메시지 삭제)
    if message.channel.id == db["channels"]["vote"] and not message.content.startswith('!'):
        await asyncio.sleep(0.5); await message.delete(); return

    await bot.process_commands(message)

# --- [6] 명령어 리스트 (도움말) ---
@bot.command(name="명령어")
async def help_cmd(ctx):
    embed = discord.Embed(title=f"🛡️ {AUTHOR} SYSTEM COMMANDS", color=0x3498db)
    embed.add_field(name="🌐 일반 유저 (General)", value="`!문의 (내용)` - 개발자 건의\n`!현황` - 시민 수 확인\n`!투표 (주제)` - 익명 투표\n`!결과` - 투표 조기 종료", inline=False)
    embed.add_field(name="🛡️ 관리자 전용 (Staff)", value="`!청소 (수)` `!추방 @유저` `!차단 @유저` `!잠금` `!해제` `!삭제` `!생성 (카테고리ID) (이름)` `!백업` `!복구`", inline=False)
    embed.add_field(name="👑 개발자 (Master)", value="`!권한부여 @유저` `!권한해제 @유저`", inline=False)
    await ctx.reply(embed=embed)

# --- [7] 관리 및 권한 명령어 ---
@bot.command(name="권한부여")
async def add_admin(ctx, member: discord.Member):
    if ctx.author.id != db["master_id"]: return
    if member.id not in db["admins"]:
        db["admins"].append(member.id); save_data()
        await ctx.reply(f"✅ {member.mention} 님이 CHUNZA 관리자로 등록되었습니다.")
    else: await ctx.reply("이미 관리자입니다.")

@bot.command(name="권한해제")
async def remove_admin(ctx, member: discord.Member):
    if ctx.author.id != db["master_id"]: return
    if member.id in db["admins"]:
        db["admins"].remove(member.id); save_data()
        await ctx.reply(f"❌ {member.mention} 님의 관리자 권한이 해제되었습니다.")

@bot.command(name="청소")
async def clear(ctx, amount: int = 10):
    if not is_auth(ctx.author): return
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 {len(deleted)-1} Messages Cleared.", delete_after=3)

@bot.command(name="잠금")
async def lock(ctx, channel: discord.TextChannel = None):
    if not is_auth(ctx.author): return
    target = channel or ctx.channel
    await target.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.reply(f"🔒 {target.mention} Locked.")

@bot.command(name="해제")
async def unlock(ctx, channel: discord.TextChannel = None):
    if not is_auth(ctx.author): return
    target = channel or ctx.channel
    await target.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.reply(f"🔓 {target.mention} Unlocked.")

@bot.command(name="추방")
async def kick(ctx, member: discord.Member):
    if not is_auth(ctx.author): return
    await member.kick(); await ctx.reply(f"👢 {member.display_name} Kicked.")

@bot.command(name="차단")
async def ban(ctx, member: discord.Member):
    if not is_auth(ctx.author): return
    await member.ban(); await ctx.reply(f"🔨 {member.display_name} Banned.")

@bot.command(name="삭제")
async def delete_ch(ctx, channel: discord.TextChannel = None):
    if not is_auth(ctx.author): return
    target = channel or ctx.channel
    await target.delete()

@bot.command(name="생성")
async def create(ctx, cat_id: int, *, name):
    if not is_auth(ctx.author): return
    cat = bot.get_channel(cat_id)
    new_ch = await ctx.guild.create_text_channel(name, category=cat)
    await ctx.reply(f"📂 {new_ch.mention} Created.")

# --- [8] 투표 및 기타 시스템 ---
@bot.command(name="투표")
async def start_vote(ctx, *, topic=None):
    if ctx.channel.id != db["channels"]["vote"]: return
    if not topic: return await ctx.reply("주제를 입력하세요.")

    q = await ctx.reply("⏰ 투표 기간 (예: 1분, 2일)")
    try:
        def check(m): return m.author == ctx.author and m.channel == ctx.channel
        msg = await bot.wait_for('message', timeout=30.0, check=check)
        t_str = msg.content; await msg.delete(); await q.delete()
        sec = int(t_str.replace('분',''))*60 if '분' in t_str else int(t_str.replace('일',''))*84600
    except: return await ctx.reply("입력 오류.")

    embed = discord.Embed(title="🗳️ 익명 투표", description=f"**주제: {topic}**", color=0xf1c40f)
    v_msg = await ctx.send(embed=embed); await v_msg.add_reaction("⭕"); await v_msg.add_reaction("❌")

    db["active_votes"][str(v_msg.id)] = {"topic":topic, "⭕":0, "❌":0, "author_id":ctx.author.id, "channel_id":ctx.channel.id}
    await asyncio.sleep(sec); await end_vote_logic(v_msg.id)

async def end_vote_logic(msg_id):
    data = db["active_votes"].pop(str(msg_id), None)
    if not data: return
    try:
        ch = bot.get_channel(data["channel_id"])
        m = await ch.fetch_message(msg_id)
        # 반응 집계
        for r in m.reactions:
            if str(r.emoji) == "⭕": data["⭕"] = r.count - 1
            if str(r.emoji) == "❌": data["❌"] = r.count - 1
        await ch.send(f"🏁 **투표 결과**\n주제: {data['topic']}\n⭕: {data['⭕']} | ❌: {data['❌']}")
        await m.delete()
    except: pass

@bot.command(name="현황")
async def status(ctx): await ctx.reply(f"📊 현재 시민 수: **{ctx.guild.member_count}명**")

@bot.command(name="문의")
async def contact(ctx, *, content=None):
    if ctx.channel.id != db["channels"]["suggestion"] or not content: return
    master = await bot.fetch_user(db["master_id"])
    await master.send(f"📩 [{ctx.author}] 문의: {content}")
    await ctx.message.delete(); await ctx.send("✅ 건의가 전달되었습니다.", delete_after=2)

@bot.command(name="백업")
async def backup_cmd(ctx):
    if not is_auth(ctx.author): return
    save_data(); await ctx.reply("💾 데이터 백업 완료.")

@bot.command(name="복구")
async def restore_cmd(ctx):
    if not is_auth(ctx.author): return
    load_data(); await ctx.reply("🛠️ 데이터 복구 완료.")

# --- [9] 웹 대시보드 및 실행 (문법 오류 수정 버전) ---
app = Flask('')

@app.route('/')
def home():
    return "CHUNZA Core Active"

def run_app():
    # Replit 환경 유지용 웹 서버 실행
    app.run(host='0.0.0.0', port=8080)

# 백그라운드에서 Flask 실행
Thread(target=run_app, daemon=True).start()

if __name__ == "__main__":
    try:
        # 입력 단계에서 받은 토큰으로 봇 구동
        bot.run(TOKEN)
    except Exception as e:
        print(f"{RED}[!] CRITICAL ERROR: {e}{RESET}")
