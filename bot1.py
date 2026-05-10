import discord
from discord.ext import commands
import os
import asyncio
import json
from datetime import timedelta
from collections import defaultdict
import time

# --- [1] 설정 및 데이터 관리 ---
MASTER_ID = 731129858629042187  
VOTE_CH_ID = 1501240737352646728 
SUGGESTION_CH_ID = 1501199686932103199 
VERIFY_CH_ID = 1501199548880650331 
DATA_FILE = "server_data.json"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

db = {
    "backup": {}, 
    "settings": {"verify_role": "시민", "verify_emoji": "✅"}, 
    "suggestion_msg_id": None,
    "admins": [681815009466253416],
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

# --- [2] 보안 및 권한 로직 ---
def is_authorized(user_id):
    return user_id == MASTER_ID or user_id in db["admins"]

async def auth_check(ctx):
    if is_authorized(ctx.author.id): return True
    await ctx.reply("🚫 **권한 부족:** 관리자 전용입니다.")
    return False

# --- [3] 메인 이벤트 ---
@bot.event
async def on_ready():
    load_data()
    print(f"==============================")
    print(f"🚀 보안 봇 온라인: {bot.user.name}")
    print(f"==============================")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id == VOTE_CH_ID and not message.content.startswith('!'):
        await asyncio.sleep(0.5); await message.delete(); return
    await bot.process_commands(message)

# --- [4] 명령어들 (기존 코드와 동일) ---

@bot.command(name="명령어")
async def help_cmd(ctx):
    embed = discord.Embed(title="📜 마롱특별시 명령어 리스트", color=0x3498db)
    embed.add_field(name="🌐 일반 유저", value="`!문의`, `!현황`, `!투표`, `!결과`", inline=False)
    embed.add_field(name="🛡️ 관리자", value="`!청소`, `!추방`, `!차단`, `!잠금`, `!해제`", inline=False)
    await ctx.reply(embed=embed)

# ... (청소, 잠금, 추방, 투표 등 나머지 명령어들 생략 - 원본 코드 유지) ...

# --- [5] 실행부 (Termux 전용) ---
if __name__ == "__main__":
    os.system('clear')
    print("==============================")
    print("🛡️ 보안 봇(bot1) 가동 시스템")
    token_input = input("▶️ 봇 토큰을 입력하세요: ").strip()
    print("==============================")
    
    if token_input:
        try:
            bot.run(token_input)
        except Exception as e:
            print(f"❌ 로그인 실패: {e}")
    else:
        print("❌ 토큰이 입력되지 않았습니다.")
