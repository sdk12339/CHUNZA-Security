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

class SecurityBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        self.target_guild_id = None

    async def setup_hook(self):
        if self.target_guild_id:
            guild = discord.Object(id=int(self.target_guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✅ [보안 봇] 서버({self.target_guild_id}) 명령어 동기화 완료!")
        else:
            await self.tree.sync()
            print("✅ [보안 봇] 글로벌 명령어 동기화 완료!")

bot = SecurityBot()

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
        json.dump(db, f, ensure_ascii=False, indent=4)

# --- [2] 권한 로직 ---
def is_authorized(user_id):
    return user_id == MASTER_ID or user_id in db["admins"]

async def auth_check(ctx):
    if is_authorized(ctx.author.id): return True
    await ctx.reply("🚫 **권한 부족:** 관리자만 사용 가능합니다.")
    return False

# --- [3] 메인 이벤트 ---
@bot.event
async def on_ready():
    print(f"🛡️ 보안 봇 가동: {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id == VOTE_CH_ID and not message.content.startswith('!'):
        await asyncio.sleep(0.5); await message.delete(); return
    await bot.process_commands(message)

# --- [4] 핵심 명령어 ---
@bot.command(name="명령어")
async def help_cmd(ctx):
    embed = discord.Embed(title="📜 마롱특별시 명령어 리스트", color=0x3498db)
    embed.add_field(name="🌐 일반 유저", value="`!문의`, `!현황`, `!투표`, `!결과`", inline=False)
    embed.add_field(name="🛡️ 관리자 전용", value="`!청소`, `!잠금`, `!해제`", inline=False)
    await ctx.reply(embed=embed)

@bot.command(name="청소")
async def clear(ctx, amount: int = 10):
    if not await auth_check(ctx): return
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 {len(deleted)-1}개 삭제 완료.", delete_after=3)

# (투표 및 기타 로직 생략 - 기존 코드 유지)

# --- [5] 가동 함수 (main.py 전용) ---
async def run_bot(token, target_guild_id):
    load_data()
    bot.target_guild_id = target_guild_id
    async with bot:
        await bot.start(token)
