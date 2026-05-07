import discord
from discord.ext import commands
import datetime
import asyncio
import os
import sys

# --- CHUNZA SECURITY TOOL INFO ---
VERSION = "v1.3.0"
AUTHOR = "CHUNZA"

def clear_screen():
    # 터미널 화면을 깨끗하게 정리합니다.
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    clear_screen()
    banner = f"""
    #################################################
    #                                               #
    #         CHUNZA SECURITY TOOL {VERSION}          #
    #         ----------------------------          #
    #    [ SYSTEM ] : SECURE PROTOCOL ACTIVE        #
    #    [ AUTHOR ] : {AUTHOR}                     #
    #                                               #
    #################################################
    """
    print(banner)

# --- 1. TOOL STARTUP & INPUT PHASE ---
print_banner()
print(f"[*] {AUTHOR} Security Tool is starting up...")
print("-" * 49)

# 여기서 먼저 입력을 받습니다.
USER_TOKEN = input("[>] Enter your Discord Bot Token: ").strip()
USER_GUILD_ID = input("[>] Enter your Target Server ID: ").strip()

print("-" * 49)
print("[*] Validating credentials and connecting to Discord...")

# --- 2. BOT CONFIGURATION ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Global Variables
TARGET_GUILD_ID = None
try:
    TARGET_GUILD_ID = int(USER_GUILD_ID)
except ValueError:
    print("[!] Error: Server ID must be numeric. Please restart.")
    sys.exit()

# --- 3. SECURITY FUNCTIONS ---

@bot.event
async def on_ready():
    print(f"[*] Login Successful: {bot.user}")
    print(f"[*] Monitoring Server ID: {TARGET_GUILD_ID}")
    print(f"[*] {AUTHOR} Security is now ARMED.")

@bot.event
async def on_member_join(member):
    if member.guild.id != TARGET_GUILD_ID: return

    # Anti-Raid: Account Age Check (3 days)
    now = datetime.datetime.now(datetime.timezone.utc)
    age = now - member.created_at
    if age.days < 3:
        try:
            await member.send(f"[{AUTHOR}] Access Denied: Account age policy.")
        except: pass
        await member.kick(reason="Anti-Raid: New Account")
        print(f"[-] Kicked: {member.name} (Age: {age.days}d)")

# Anti-Spam & Link Filter
@bot.event
async def on_message(message):
    if message.author.bot or message.guild.id != TARGET_GUILD_ID: return

    # Link Filter
    if "discord.gg/" in message.content.lower() or "http" in message.content.lower():
        if not message.author.guild_permissions.administrator:
            await message.delete()
            return

    await bot.process_commands(message)

# Role & Admin Monitoring
@bot.event
async def on_guild_role_create(role):
    if role.guild.id != TARGET_GUILD_ID: return
    if role.permissions.administrator:
        print(f"[ALERT] High Privilege Role Created: {role.name}")

@bot.event
async def on_member_update(before, after):
    if after.guild.id != TARGET_GUILD_ID: return
    if not before.guild_permissions.administrator and after.guild_permissions.administrator:
        print(f"[CRITICAL] Admin Granted to: {after.name}")

# --- 4. EXECUTION ---
if __name__ == "__main__":
    try:
        # 입력받은 토큰으로 봇을 실행합니다.
        bot.run(USER_TOKEN)
    except discord.errors.LoginFailure:
        print("\n[!] LOGIN FAILED: The token you entered is invalid.")
        print("[!] Please check your token at Discord Developer Portal.")
    except Exception as e:
        print(f"\n[!] AN ERROR OCCURRED: {e}")
