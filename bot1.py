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
    await ctx.reply("🚫 **권한 부족:** 관리자만 사용 가능합니다.")
    return False

# --- [3] 메인 이벤트 ---
@bot.event
async def on_ready():
    load_data()
    print(f"🚀 {bot.user.name} (Bot 1) 가동 시작")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id == VOTE_CH_ID and not message.content.startswith('!'):
        await asyncio.sleep(0.5); await message.delete(); return
    await bot.process_commands(message)

# --- [4] 명령어 리스트 (도움말) ---
@bot.command(name="명령어")
async def help_cmd(ctx):
    embed = discord.Embed(title="📜 마롱특별시 명령어 리스트", color=0x3498db)
    embed.add_field(name="🌐 일반 유저", value="`!문의`, `!현황`, `!투표`, `!결과`", inline=False)
    embed.add_field(name="🛡️ 관리자 전용", value="`!청소`, `!추방`, `!차단`, `!잠금`, `!해제`, `!삭제`, `!생성`, `!백업`, `!복구`", inline=False)
    embed.add_field(name="👑 개발자 전용", value="`!권한부여`, `!권한해제`", inline=False)
    await ctx.reply(embed=embed)

# --- [5] 관리 및 투표 핵심 명령어 (기존 로직 유지) ---
@bot.command(name="권한부여")
async def add_admin(ctx, member: discord.Member):
    if ctx.author.id != MASTER_ID: return await ctx.reply("👑 Master 전용.")
    if member.id not in db["admins"]:
        db["admins"].append(member.id); save_data()
        await ctx.reply(f"✅ {member.mention} 관리자 임명.")

@bot.command(name="권한해제")
async def remove_admin(ctx, member: discord.Member):
    if ctx.author.id != MASTER_ID: return await ctx.reply("👑 Master 전용.")
    if member.id in db["admins"]:
        db["admins"].remove(member.id); save_data()
        await ctx.reply(f"❌ {member.mention} 관리자 해임.")

@bot.command(name="청소")
async def clear(ctx, amount: int = 10):
    if not await auth_check(ctx): return
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 {len(deleted)-1}개 삭제 완료.", delete_after=3)

@bot.command(name="잠금")
async def lock(ctx, channel: discord.TextChannel = None):
    if not await auth_check(ctx): return
    target = channel or ctx.channel
    await target.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.reply(f"🔒 {target.mention} 잠금 완료.")

@bot.command(name="해제")
async def unlock(ctx, channel: discord.TextChannel = None):
    if not await auth_check(ctx): return
    target = channel or ctx.channel
    await target.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.reply(f"🔓 {target.mention} 해제 완료.")

@bot.command(name="투표")
async def start_vote(ctx, *, topic=None):
    if ctx.channel.id != VOTE_CH_ID: return await ctx.reply("❌ 투표 전용 채널을 이용하세요.")
    if not topic: return await ctx.reply("주제를 입력하세요.")
    q = await ctx.reply("⏰ 기간 입력 (예: 1분, 2일)")
    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
        t_str = msg.content; await msg.delete(); await q.delete()
        if '분' in t_str: sec = int(t_str.replace('분',''))*60
        elif '일' in t_str: sec = int(t_str.replace('일',''))*84600
        else: return await ctx.reply("형식 오류.")
    except: return await ctx.reply("시간 초과.")
    embed = discord.Embed(title="🗳️ 익명 투표", description=f"**주제: {topic}**", color=0xf1c40f)
    embed.add_field(name="찬성 (⭕)", value="0표", inline=True)
    embed.add_field(name="거절 (❌)", value="0표", inline=True)
    v_msg = await ctx.send(embed=embed); await v_msg.add_reaction("⭕"); await v_msg.add_reaction("❌")
    await ctx.message.delete()
    db["active_votes"][str(v_msg.id)] = {"topic":topic, "⭕":0, "❌":0, "voters":{}, "author_id":ctx.author.id, "channel_id":ctx.channel.id}
    await asyncio.sleep(sec); await end_vote_logic(v_msg.id)

@bot.command(name="결과")
async def quick_result(ctx):
    for m_id, data in list(db["active_votes"].items()):
        if data["author_id"] == ctx.author.id:
            await ctx.message.delete(); await end_vote_logic(int(m_id)); return
    await ctx.reply("진행 중인 투표가 없습니다.")

async def end_vote_logic(msg_id):
    data = db["active_votes"].pop(str(msg_id), None)
    if not data: return
    ch = bot.get_channel(data["channel_id"])
    try:
        m = await ch.fetch_message(msg_id)
        await ch.send(f"🏁 **투표 종료**\n주제: {data['topic']}\n⭕: {data['⭕']} | ❌: {data['❌']}", delete_after=10)
        await m.delete()
    except: pass

@bot.command(name="현황")
async def status(ctx): await ctx.reply(f"📊 시민 수: **{ctx.guild.member_count}명**")

@bot.command(name="문의")
async def contact(ctx, *, content=None):
    if ctx.channel.id != SUGGESTION_CH_ID or not content: return
    master = await bot.fetch_user(MASTER_ID)
    await master.send(f"📩 [{ctx.author}] 문의: {content}")
    await ctx.message.delete(); await ctx.send("✅ 전달 완료.", delete_after=2)

# --- [6] 실행 함수 (main.py에서 호출) ---
def run_bot():
    # 여기에 봇 1번의 토큰을 직접 입력하세요
    MY_TOKEN = "여기에_봇1_토큰_입력" 
    bot.run(MTUwMDI1NTgzOTI5Mjg4MzA5NQ.G3bNE2.0M8cQLriex4iv2_eO0FFodKbS-kRFpth51MZzc)

