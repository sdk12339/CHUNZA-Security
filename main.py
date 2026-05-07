import discord
from discord.ext import commands
import datetime
import asyncio
import os
import sys

# --- UI SETTINGS ---
VERSION = "v1.4.0"
CYAN = "\033[96m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    clear_screen()
    # 'CHUNZA'를 강조한 아스키 아트 스타일 배너
    banner = f"""
{CYAN}{BOLD}
    ██████╗██╗  ██╗██╗   ██╗███╗   ██╗███████╗ █████╗ 
   ██╔════╝██║  ██║██║   ██║████╗  ██║╚══███╔╝██╔══██╗
   ██║     ███████║██║   ██║██╔██╗ ██║  ███╔╝ ███████║
   ██║     ██╔══██║██║   ██║██║╚██╗██║ ███╔╝  ██╔══██║
   ╚██████╗██║  ██║╚██████╔╝██║ ╚████║███████╗██║  ██║
    ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
{RESET}
          {YELLOW}>> SYSTEM ARMED & READY | VERSION: {VERSION} <<{RESET}
          {YELLOW}>>        PROTECTION CORE: ACTIVATED        <<{RESET}
    """
    print(banner)

# --- STARTUP ---
print_banner()
print(f"{GREEN}[*] INITIALIZING CHUNZA KERNEL...{RESET}")
TOKEN = input(f"{CYAN}[>] INPUT BOT TOKEN: {RESET}").strip()
GUILD_INPUT = input(f"{CYAN}[>] INPUT TARGET SERVER ID: {RESET}").strip()

try:
    TARGET_GUILD_ID = int(GUILD_INPUT)
except:
    print(f"{RED}[!] FATAL: INVALID SERVER ID.{RESET}")
    sys.exit()

# --- BOT CORE ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

# 스팸 데이터 저장소
spam_data = {} # {user_id: [timestamps]}

@bot.event
async def on_ready():
    print_banner()
    print(f"{GREEN}[+] CONNECTION ESTABLISHED: {bot.user}{RESET}")
    print(f"{GREEN}[+] TARGET ENCRYPTED ID: {TARGET_GUILD_ID}{RESET}")
    print(f"{CYAN}[!] CHUNZA IS WATCHING THE SERVER...{RESET}\n")

# --- 1. SPAM & LINK CONTROL (FIXED) ---
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    if message.guild.id != TARGET_GUILD_ID: return

    # [수정] 스팸 감지 로직: 3초 안에 4번 메시지 시 차단
    user_id = message.author.id
    now = datetime.datetime.now()

    if user_id not in spam_data:
        spam_data[user_id] = []

    spam_data[user_id].append(now)
    # 3초 이내의 메시지만 필터링
    spam_data[user_id] = [t for t in spam_data[user_id] if (now - t).total_seconds() < 3]

    if len(spam_data[user_id]) > 4:
        await message.delete()
        # 관리자가 아닐 때만 경고 메시지 전송
        if not message.author.guild_permissions.administrator:
            await message.channel.send(f"**{message.author.name}**, [CHUNZA] SPAM DETECTED. SLOW DOWN.", delete_after=2)
            print(f"{RED}[SPAM] Detected from {message.author.name}{RESET}")
            return # 스팸이면 아래 링크 검사 생략

    # 링크 차단 (관리자 제외)
    if "http" in message.content.lower() or "discord.gg/" in message.content.lower():
        if not message.author.guild_permissions.administrator:
            await message.delete()
            print(f"{YELLOW}[LINK] Filtered from {message.author.name}{RESET}")

    await bot.process_commands(message)

# --- 2. AUTH & ANTI-RAID ---
@bot.event
async def on_member_join(member):
    if member.guild.id != TARGET_GUILD_ID: return

    # 신규 계정 자동 추방 (3일 미만)
    age = datetime.datetime.now(datetime.timezone.utc) - member.created_at
    if age.days < 3:
        await member.kick(reason="CHUNZA: New Account Protection")
        print(f"{RED}[KICK] New Account: {member.name} ({age.days}d){RESET}")

# --- 3. SYSTEM LOGGING ---
@bot.event
async def on_guild_role_create(role):
    if role.guild.id != TARGET_GUILD_ID: return
    if role.permissions.administrator:
        print(f"{RED}[CRITICAL] ADMIN ROLE CREATED: {role.name}{RESET}")

@bot.event
async def on_member_update(before, after):
    if after.guild.id != TARGET_GUILD_ID: return
    if not before.guild_permissions.administrator and after.guild_permissions.administrator:
        print(f"{RED}[ALERT] ADMIN PERMISSION GRANTED: {after.name}{RESET}")

# --- EXECUTE ---
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"{RED}[!] CRITICAL ERROR: {e}{RESET}")
