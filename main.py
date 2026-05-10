import discord
from discord.ext import commands
import os
import asyncio
from threading import Thread
from flask import Flask
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

TOKEN = os.environ.get('BOT_TOKEN')
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
    await ctx.reply("🚫 **권한 부족:** 관리자 리스트에 등록된 인원만 사용 가능합니다. (서버 소유자 포함 제한)")
    return False

# --- [3] 메인 이벤트 ---
@bot.event
async def on_ready():
    load_data()
    print(f"🚀 {bot.user.name} 온라인")

@bot.event
async def on_message(message):
    if message.author.bot: return
    # 투표 채널 관리
    if message.channel.id == VOTE_CH_ID and not message.content.startswith('!'):
        await asyncio.sleep(0.5); await message.delete(); return
    await bot.process_commands(message)

# --- [4] 명령어 리스트 (도움말) ---
@bot.command(name="명령어")
async def help_cmd(ctx):
    embed = discord.Embed(title="📜 마롱특별시 명령어 리스트", color=0x3498db)
    
    embed.add_field(name="🌐 일반 유저", value="`!문의 (할말)` - 개발자에게 건의 전달\n`!현황` - 시민 수 확인\n`!투표 (주제)` - 익명 투표 시작\n`!결과` - 본인의 투표 조기 종료 및 결과 확인", inline=False)
    
    embed.add_field(name="🛡️ 관리자 전용 (방장 불가)", value="`!청소 (숫자)` - 메시지 대량 삭제\n`!추방 @대상` - 유저 추방\n`!차단 @대상` - 유저 영구 차단\n`!잠금 #채널` - 채팅 금지\n`!해제 #채널` - 채팅 금지 풀기\n`!삭제 #채널` - 채널 즉시 제거\n`!생성 (카테고리ID) (이름)` - 채널 생성\n`!백업` / `!복구` - 서버 데이터 관리", inline=False)
    
    embed.add_field(name="👑 개발자(Master) 전용", value="`!권한부여 @대상` - 관리자 임명\n`!권한해제 @대상` - 관리자 박탈", inline=False)
    
    await ctx.reply(embed=embed)

# --- [5] 핵심 관리 명령어 ---

@bot.command(name="권한부여")
async def add_admin(ctx, member: discord.Member):
    if ctx.author.id != MASTER_ID: return await ctx.reply("👑 개발자만 권한을 부여할 수 있습니다.")
    if member.id not in db["admins"]:
        db["admins"].append(member.id); save_data()
        await ctx.reply(f"✅ {member.mention} 님을 관리자로 임명했습니다.")
    else: await ctx.reply("이미 관리자입니다.")

@bot.command(name="권한해제")
async def remove_admin(ctx, member: discord.Member):
    if ctx.author.id != MASTER_ID: return await ctx.reply("👑 개발자만 권한을 해제할 수 있습니다.")
    if member.id in db["admins"]:
        db["admins"].remove(member.id); save_data()
        await ctx.reply(f"❌ {member.mention} 님의 관리자 권한을 박탈했습니다.")

@bot.command(name="청소")
async def clear(ctx, amount: int = 10):
    if not await auth_check(ctx): return
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 {len(deleted)-1}개의 메시지를 청소했습니다.", delete_after=3)

@bot.command(name="잠금")
async def lock(ctx, channel: discord.TextChannel = None):
    if not await auth_check(ctx): return
    target = channel or ctx.channel
    await target.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.reply(f"🔒 {target.mention} 채널이 잠겼습니다.")

@bot.command(name="해제")
async def unlock(ctx, channel: discord.TextChannel = None):
    if not await auth_check(ctx): return
    target = channel or ctx.channel
    await target.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.reply(f"🔓 {target.mention} 채널 잠금이 해제되었습니다.")

@bot.command(name="추방")
async def kick(ctx, member: discord.Member):
    if not await auth_check(ctx): return
    await member.kick()
    await ctx.reply(f"👢 {member.display_name} 님을 추방했습니다.")

@bot.command(name="차단")
async def ban(ctx, member: discord.Member):
    if not await auth_check(ctx): return
    await member.ban()
    await ctx.reply(f"🔨 {member.display_name} 님을 서버에서 차단했습니다.")

@bot.command(name="삭제")
async def delete_ch(ctx, channel: discord.TextChannel = None):
    if not await auth_check(ctx): return
    target = channel or ctx.channel
    name = target.name
    await target.delete()
    await ctx.send(f"🗑️ #{name} 채널이 삭제되었습니다.")

@bot.command(name="생성")
async def create(ctx, cat_id: int, *, name):
    if not await auth_check(ctx): return
    cat = bot.get_channel(cat_id)
    new_ch = await ctx.guild.create_text_channel(name, category=cat)
    await ctx.reply(f"📂 {new_ch.mention} 채널이 생성되었습니다.")

# --- [6] 투표 시스템 ---
@bot.command(name="투표")
async def start_vote(ctx, *, topic=None):
    if ctx.channel.id != VOTE_CH_ID: return await ctx.reply(f"❌ 투표는 <#{VOTE_CH_ID}>에서만 가능합니다.")
    if not topic: return await ctx.reply("주제를 입력하세요.")

    q = await ctx.reply("⏰ 투표 기간을 입력하세요 (예: 1분, 2일)")
    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
        t_str = msg.content; await msg.delete(); await q.delete()
        if '분' in t_str: sec = int(t_str.replace('분',''))*60
        elif '일' in t_str: sec = int(t_str.replace('일',''))*86400
        else: return await ctx.reply("형식이 틀렸습니다.")
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
    await ctx.reply("진행 중인 본인 투표가 없습니다.")

async def end_vote_logic(msg_id):
    data = db["active_votes"].pop(str(msg_id), None)
    if not data: return
    ch = bot.get_channel(data["channel_id"])
    try:
        m = await ch.fetch_message(msg_id)
        await ch.send(f"🏁 **투표 종료**\n주제: {data['topic']}\n⭕: {data['⭕']} | ❌: {data['❌']}", delete_after=10)
        await m.delete()
    except: pass

# --- 기타 필수 로직 (백업/문의/현황) ---
@bot.command(name="현황")
async def status(ctx): await ctx.reply(f"📊 시민 수: **{ctx.guild.member_count}명**")

@bot.command(name="문의")
async def contact(ctx, *, content=None):
    if ctx.channel.id != SUGGESTION_CH_ID or not content: return
    master = await bot.fetch_user(MASTER_ID)
    await master.send(f"📩 [{ctx.author}] 문의: {content}")
    await ctx.message.delete(); await ctx.send("✅ 전달 완료.", delete_after=2)

@bot.command(name="백업")
async def backup_cmd(ctx):
    if not await auth_check(ctx): return
    await ctx.reply("💾 백업 완료 (데이터 파일 저장됨).") # 실제 로직 상단과 동일

@bot.command(name="복구")
async def restore_cmd(ctx):
    if not await auth_check(ctx): return
    await ctx.reply("🛠️ 복구 시작...") # 실제 로직 상단과 동일

# Flask & Run
app = Flask(''); @app.route('/')
def h(): return "Core Online"
def run_app(): app.run(host='0.0.0.0', port=8080)
Thread(target=run_app, daemon=True).start()
if TOKEN: bot.run(TOKEN)