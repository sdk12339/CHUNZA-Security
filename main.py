import discord
from discord.ext import commands
import datetime
import re
import asyncio

# --- 설정 (Config) ---
TOKEN = "YOUR_BOT_TOKEN_HERE"
LOG_CHANNEL_ID = 123456789012345678  # 로그를 남길 채널 ID
MIN_ACCOUNT_AGE_DAYS = 3  # 계정 생성 제한일
ALLOWED_LINKS = ["discord.gg/my-server"] # 허용된 링크 리스트

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# --- 1. 입장 및 신원 인증 (Anti-Raid & Auth) ---
@bot.event
async def on_member_join(member):
    # 계정 생성일 제한
    now = datetime.datetime.now(datetime.timezone.utc)
    account_age = now - member.created_at
    if account_age.days < MIN_ACCOUNT_AGE_DAYS:
        await member.send(f"Your account is too new ({account_age.days} days). Min requirement: {MIN_ACCOUNT_AGE_DAYS} days.")
        await member.kick(reason="New account protection")
        return

    # 캡차(CAPTCHA) 및 역할 부여
    await member.send("Welcome to CHUNZA Security. Please complete the verification.")
    # 실제 구현 시 캡차 이미지를 생성하여 전송하는 로직이 추가됩니다.

# --- 2. 채팅 및 콘텐츠 필터링 (Anti-Spam & Content) ---
user_messages = {}

@bot.event
async def on_message(message):
    if message.author.bot: return

    # 스팸 방지 (5초 내 5개 메시지)
    user_id = message.author.id
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(datetime.datetime.now())

    recent_msgs = [m for m in user_messages[user_id] if (datetime.datetime.now() - m).seconds < 5]
    if len(recent_msgs) > 5:
        await message.channel.send(f"{message.author.mention}, Stop spamming!", delete_after=3)
        await message.delete()
        return

    # 링크 차단
    if "https://" in message.content or "http://" in message.content:
        if not any(link in message.content for link in ALLOWED_LINKS):
            await message.delete()
            await message.channel.send("Unauthorized links are prohibited.", delete_after=5)
            return

    await bot.process_commands(message)

# --- 3. 서버 관리 및 모니터링 (Moderation & Log) ---
@bot.event
async def on_member_remove(member):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    embed = discord.Embed(title="Member Left", color=discord.Color.red())
    embed.add_field(name="User", value=f"{member.name} ({member.id})")
    await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_create(role):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if role.permissions.administrator:
        await log_channel.send(f"⚠️ **WARNING**: New Admin role created: {role.name}")

# --- 4. 위협 탐지 (Threat Detection) ---
@bot.event
async def on_member_update(before, after):
    # 관리자 권한 변동 감시
    if not before.guild_permissions.administrator and after.guild_permissions.administrator:
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(f"🚨 **CRITICAL**: {after.mention} granted Administrator permissions!")

# --- CHUNZA Banner ---
@bot.event
async def on_ready():
    banner = f"""
    #########################################
    #          CHUNZA SECURITY TOOL         #
    #    -------------------------------    #
    #    Status: ONLINE                     #
    #    User: {bot.user}             #
    #########################################
    """
    print(banner)

# Replit run 버튼을 누르지 않아도 되도록 실행 코드는 유지하되, Termux에서 실행 시 적용됩니다.
if __name__ == "__main__":
    bot.run(TOKEN)
