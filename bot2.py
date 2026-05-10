import discord
from discord.ext import commands, tasks
import asyncio
import sqlite3
import random
import datetime
import os
from discord import app_commands

# --- [1] 설정 및 초기화 ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

# DB 연결
db = sqlite3.connect('chunja_economy.db')
cursor = db.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        money INTEGER DEFAULT 30000,
        bankruptcy_papers INTEGER DEFAULT 5,
        attendance_count INTEGER DEFAULT 0,
        last_attendance TEXT,
        last_daily_money TEXT,
        macaron_exp INTEGER DEFAULT 0,
        work_exp INTEGER DEFAULT 0,
        dig_exp INTEGER DEFAULT 0,
        weapon_lv INTEGER DEFAULT 1,
        weapon_durability INTEGER DEFAULT 100,
        weapon_piece INTEGER DEFAULT 0,
        stars INTEGER DEFAULT 0,
        transfer_count INTEGER DEFAULT 10,
        last_transfer_reset TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS macarons (
        user_id INTEGER PRIMARY KEY,
        normal INTEGER DEFAULT 0,
        super INTEGER DEFAULT 0,
        legend INTEGER DEFAULT 0,
        heaven INTEGER DEFAULT 0
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS savings (
        user_id INTEGER PRIMARY KEY,
        plan_type TEXT,
        amount INTEGER DEFAULT 0,
        join_date TEXT
    )''')
    db.commit()

# --- [2] 메인 이벤트 및 태스크 ---
@bot.event
async def on_ready():
    init_db()
    await bot.tree.sync()
    if not midnight_tasks.is_running():
        midnight_tasks.start()
    print(f"==============================")
    print(f"🌸 춘자 경제 봇 온라인: {bot.user.name}")
    print(f"==============================")

@tasks.loop(minutes=1)
async def midnight_tasks():
    now = datetime.datetime.now()
    if now.hour == 0 and now.minute == 0:
        cursor.execute("UPDATE users SET money = CAST(money * 0.9 AS INTEGER) WHERE money >= 100000000")
        db.commit()
        print("💰 [시스템] 자정 세금 정산 완료!")

# --- [3] 경제 시스템 명령어 ---

@bot.tree.command(name="가입", description="춘자 경제 시스템에 가입합니다.")
async def join(interaction: discord.Interaction):
    user_id = interaction.user.id
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone():
        await interaction.response.send_message("이미 가입되어 있다구! 🌸", ephemeral=True)
    else:
        cursor.execute("INSERT INTO users (id, money, bankruptcy_papers) VALUES (?, 30000, 5)", (user_id,))
        cursor.execute("INSERT INTO macarons (user_id) VALUES (?)", (user_id,))
        db.commit()
        await interaction.response.send_message(f"🎉 {interaction.user.mention}! 가입 선물로 **30,000원**과 **파산신청서 5장**을 지급했어!")

@bot.tree.command(name="돈줘", description="1,000원을 받습니다.")
async def get_money(interaction: discord.Interaction):
    user_id = interaction.user.id
    cursor.execute("UPDATE users SET money = money + 1000 WHERE id = ?", (user_id,))
    db.commit()
    await interaction.response.send_message("🌸 춘자가 용돈 **1,000원**을 줬어!")

@bot.tree.command(name="마카롱", description="마카롱을 굽습니다.")
async def make_macaron(interaction: discord.Interaction):
    cursor.execute("SELECT macaron_exp FROM users WHERE id = ?", (interaction.user.id,))
    exp = cursor.fetchone()[0]
    success_rate = 0.60
    if random.random() <= success_rate:
        cursor.execute("UPDATE macarons SET normal = normal + 1 WHERE user_id = ?", (interaction.user.id,))
        cursor.execute("UPDATE users SET macaron_exp = macaron_exp + 1 WHERE id = ?", (interaction.user.id,))
        await interaction.response.send_message(f"🧁 **성공!** 일반 마카롱을 구웠어!")
    else:
        loss = random.randint(1000, 2000)
        cursor.execute("UPDATE users SET money = money - ? WHERE id = ?", (loss, interaction.user.id,))
        await interaction.response.send_message(f"💥 **실패...** 재료비 {loss}원을 잃었어.")
    db.commit()

@bot.tree.command(name="배치", description="롤 티어 배치를 봅니다.")
@app_commands.describe(bet="베팅할 금액")
async def rank_game(interaction: discord.Interaction, bet: int):
    if bet < 1000: return await interaction.response.send_message("최소 1,000원 이상 베팅해!", ephemeral=True)
    result_rank = "🟡 골드"
    reward = bet * 1
    cursor.execute("UPDATE users SET money = money + ? WHERE id = ?", (reward, interaction.user.id))
    db.commit()
    await interaction.response.send_message(f"🎮 배치 결과: **{result_rank}**! 보상: {reward:,}원")

@bot.tree.command(name="강화", description="무기를 강화합니다.")
async def upgrade_weapon(interaction: discord.Interaction):
    cursor.execute("SELECT weapon_lv, money FROM users WHERE id = ?", (interaction.user.id,))
    lv, money = cursor.fetchone()
    cost = 1000
    if money < cost: return await interaction.response.send_message("돈이 부족해!", ephemeral=True)
    if random.random() < 0.90:
        cursor.execute("UPDATE users SET weapon_lv = weapon_lv + 1, money = money - ? WHERE id = ?", (cost, interaction.user.id))
        await interaction.response.send_message(f"⚔️ 강화 성공! Lv.{lv+1}")
    else:
        await interaction.response.send_message("🛡️ 강화 실패...")
    db.commit()

# --- [4] 관리자 전용 명령어 ---
@bot.command(name="돈받기")
@commands.is_owner()
async def admin_give_money(ctx, amount: int):
    cursor.execute("UPDATE users SET money = money + ? WHERE id = ?", (amount, ctx.author.id))
    db.commit()
    await ctx.send(f"💰 {amount:,}원을 획득했습니다.")

# --- [5] 실행부 ---
if __name__ == "__main__":
    os.system('clear')
    print("==============================")
    print("🌸 춘자 봇(bot2) 가동 시스템")
    token_input = input("▶️ 봇 토큰을 입력하세요: ").strip()
    print("==============================")
    if token_input:
        bot.run(token_input)
    else:
        print("❌ 토큰 미입력.")
