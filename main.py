import discord
from discord.ext import commands
import datetime
import asyncio
import os
import sys
import json

# --- [1] 정보 및 색상 설정 ---
VERSION = "v1.5.0"
AUTHOR = "CHUNZA"
DATA_FILE = "server_data.json"

CYAN = "\033[96m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

# --- [2] 데이터 로드/저장 ---
db = {
    "admins": [681815009466253416], # 초기 관리자 ID
    "master_id": 731129858629042187,
    "vote_ch_id": None,
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

# --- [3] UI 및 배너 ---
def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""{CYAN}{BOLD}
    ██████╗██╗  ██╗██╗   ██╗███╗   ██╗███████╗ █████╗ 
   ██╔════╝██║  ██║██║   ██║████╗  ██║╚══███╔╝██╔══██╗
   ██║     ███████║██║   ██║██╔██╗ ██║  ███╔╝ ███████║
   ██║     ██╔══██║██║   ██║██║╚██╗██║ ███╔╝  ██╔══██║
   ╚██████╗██║  ██║╚██████╔╝██║ ╚████║███████╗██║  ██║
    ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝{RESET}
          {YELLOW}>> CHUNZA GRAND UPDATE | {VERSION} <<{RESET}
          {YELLOW}>> SECURITY & MANAGEMENT CORE ACTIVE <<{RESET}
    """)

# --- [4] 봇 초기 설정 ---
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
spam_data = {}

# --- [5] 권한 체크 유틸리티 ---
def is_auth(user_id):
    return user_id == db["master_id"] or user_id in db["admins"]

# --- [6] 이벤트 핸들러 ---
@bot.event
async def on_ready():
    load_data()
    print_banner()
    print(f"{GREEN}[+] CHUNZA ONLINE: {bot.user}{RESET}")
    print(f"{GREEN}[+] MASTER ID: {db['master_id']}{RESET}")
    print(f"{CYAN}[!] SECURITY SYSTEMS ARMED.{RESET}\n")

@bot.event
async def on_member_join(member):
    if member.guild.id != TARGET_GUILD_ID: return
    # 신규 계정 보호 (3일)
    age = datetime.datetime.now(datetime.timezone.utc) - member.created_at
    if age.days < 3:
        await member.kick(reason="CHUNZA: New Account Protection")
        print(f"{RED}[KICK] {member.name} (Age: {age.days}d){RESET}")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    if message.guild.id != TARGET_GUILD_ID: return

    # 투표 채널 잡채팅 자동 삭제
    if db["vote_ch_id"] and message.channel.id == db["vote_ch_id"]:
        if not message.content.startswith('!'):
            await asyncio.sleep(0.5)
            await message.delete()
            return

    # 스팸 방지 (3초 4회)
    uid = message.author.id
    now = datetime.datetime.now()
    if uid not in spam_data: spam_data[uid] = []
    spam_data[uid].append(now)
    spam_data[uid] = [t for t in spam_data[uid] if (now - t).total_seconds() < 3]

    if len(spam_data[uid]) > 4:
        await message.delete()
        if not is_auth(uid):
            await message.channel.send(f"**{message.author.name}**, [CHUNZA] STOP SPAMMING.", delete_after=2)
            print(f"{RED}[SPAM] {message.author.name}{RESET}")
            return

    # 링크 차단
    if "http" in message.content.lower() or "discord.gg/" in message.content.lower():
        if not is_auth(uid):
            await message.delete()
            print(f"{YELLOW}[LINK] {message.author.name}{RESET}")

    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(p):
    if p.user_id == bot.user.id: return
    msg_id = str(p.message_id)
    if msg_id not in db["active_votes"]: return

    vote_data = db["active_votes"][msg_id]
    emoji = str(p.emoji)
    if emoji not in ["⭕", "❌"]: return

    guild = bot.get_guild(p.guild_id)
    channel = bot.get_channel(p.channel_id)
    user = guild.get_member(p.user_id)

    # 반응 삭제 (익명성 유지)
    try:
        msg = await channel.fetch_message(p.message_id)
        await msg.remove_reaction(p.emoji, user)
    except: pass

    if str(p.user_id) in vote_data["voters"]: return

    vote_data["voters"][str(p.user_id)] = emoji
    vote_data[emoji] += 1

    # 임베드 업데이트
    embed = msg.embeds[0]
    embed.set_field_at(0, name="YES (⭕)", value=f"{vote_data['⭕']} Votes", inline=True)
    embed.set_field_at(1, name="NO (❌)", value=f"{vote_data['❌']} Votes", inline=True)
    await msg.edit(embed=embed)

    # 마스터에게 로그 전송
    master = await bot.fetch_user(db["master_id"])
    await master.send(f"📊 [VOTE] {user.name} voted {emoji} | Topic: {vote_data['topic']}")

# --- [7] 명령어서 - 투표 및 관리 ---

@bot.command(name="투표채널")
async def set_vote_ch(ctx):
    if not is_auth(ctx.author.id): return
    db["vote_ch_id"] = ctx.channel.id
    save_data()
    await ctx.send(f"{GREEN}[CHUNZA] Vote channel set to {ctx.channel.mention}{RESET}")

@bot.command(name="투표")
async def start_vote(ctx, *, topic=None):
    if not db["vote_ch_id"] or ctx.channel.id != db["vote_ch_id"]:
        return await ctx.send("❌ Use the designated vote channel.", delete_after=3)
    if not topic: return await ctx.send("📝 Enter a topic.", delete_after=3)

    q = await ctx.send("⏰ Duration? (e.g., '1분' or '2일')")
    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    try:
        msg = await bot.wait_for('message', timeout=20.0, check=check)
        time_str = msg.content
        if '분' in time_str: sec = int(time_str.replace('분','')) * 60
        elif '일' in time_str: sec = int(time_str.replace('일','')) * 86400
        else: raise Exception()
        await msg.delete(); await q.delete()
    except:
        return await ctx.send("⌛ Vote Cancelled.", delete_after=3)

    embed = discord.Embed(title="🗳️ ANONYMOUS VOTE", description=f"**Topic: {topic}**", color=0x3498db)
    embed.add_field(name="YES (⭕)", value="0 Votes", inline=True)
    embed.add_field(name="NO (❌)", value="0 Votes", inline=True)
    embed.set_footer(text=f"Ends in: {time_str} | By: {ctx.author.name}")

    v_msg = await ctx.send(embed=embed)
    await v_msg.add_reaction("⭕")
    await v_msg.add_reaction("❌")

    db["active_votes"][str(v_msg.id)] = {
        "topic": topic, "⭕": 0, "❌": 0, "voters": {}, 
        "author_id": ctx.author.id, "channel_id": ctx.channel.id
    }
    await ctx.message.delete()

    await asyncio.sleep(sec)
    await end_vote(v_msg.id)

async def end_vote(msg_id):
    data = db["active_votes"].pop(str(msg_id), None)
    if not data: return
    channel = bot.get_channel(data["channel_id"])
    try:
        res = f"🏁 **VOTE ENDED: {data['topic']}**\n⭕ YES: {data['⭕']} | ❌ NO: {data['❌']}"
        await channel.send(res)
        msg = await channel.fetch_message(msg_id)
        await msg.delete()
    except: pass

@bot.command(name="청소")
async def clear(ctx, amount: int = 10):
    if not is_auth(ctx.author.id): return
    await ctx.channel.purge(limit=amount + 1)
    print(f"{CYAN}[CLEAN] {ctx.author.name} cleared {amount} messages.{RESET}")

@bot.command(name="권한부여")
async def add_admin(ctx, member: discord.Member):
    if ctx.author.id != db["master_id"]: return
    if member.id not in db["admins"]:
        db["admins"].append(member.id)
        save_data(); await ctx.send(f"✅ {member.mention} is now Admin.")

# --- [8] 보안 모니터링 ---
@bot.event
async def on_guild_role_create(role):
    if role.guild.id != TARGET_GUILD_ID: return
    if role.permissions.administrator:
        print(f"{RED}[CRITICAL] ADMIN ROLE CREATED: {role.name}{RESET}")

@bot.event
async def on_member_update(before, after):
    if after.guild.id != TARGET_GUILD_ID: return
    if not before.guild_permissions.administrator and after.guild_permissions.administrator:
        print(f"{RED}[ALERT] ADMIN PRIVILEGE GRANTED: {after.name}{RESET}")

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"{RED}[!] ERROR: {e}{RESET}")
