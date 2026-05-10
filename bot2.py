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
    # 유저 정보 테이블 (문서 내 모든 기능 반영)
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
    # 마카롱 인벤토리
    cursor.execute('''CREATE TABLE IF NOT EXISTS macarons (
        user_id INTEGER PRIMARY KEY,
        normal INTEGER DEFAULT 0,
        super INTEGER DEFAULT 0,
        legend INTEGER DEFAULT 0,
        heaven INTEGER DEFAULT 0
    )''')
    # 적금 시스템
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
    print(f"🌸 춘자 통합 시스템 온라인: {bot.user.name}")
    print(f"==============================")

@tasks.loop(minutes=1)
async def midnight_tasks():
    now = datetime.datetime.now()
    # 자정 세금 정산 및 초기화
    if now.hour == 0 and now.minute == 0:
        cursor.execute("UPDATE users SET money = CAST(money * 0.9 AS INTEGER) WHERE money >= 100000000")
        cursor.execute("UPDATE users SET transfer_count = 10")
        db.commit()

# --- [3] 경제 및 보상 명령어 ---

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
        await interaction.response.send_message(f"🎉 가입 완료! 선물로 **30,000원**과 **파산신청서 5장**을 줬어!")

@bot.tree.command(name="돈줘", description="10분에 한 번 1,000원을 받습니다.")
async def get_money(interaction: discord.Interaction):
    user_id = interaction.user.id
    cursor.execute("SELECT last_daily_money FROM users WHERE id = ?", (user_id,))
    last_time_str = cursor.fetchone()[0]
    
    now = datetime.datetime.now()
    if last_time_str:
        last_time = datetime.datetime.fromisoformat(last_time_str)
        if now < last_time + datetime.timedelta(minutes=10):
            remain = (last_time + datetime.timedelta(minutes=10) - now).seconds // 60
            return await interaction.response.send_message(f"아직은 안 돼! {remain}분 뒤에 다시 와 🌸", ephemeral=True)

    cursor.execute("UPDATE users SET money = money + 1000, last_daily_money = ? WHERE id = ?", (now.isoformat(), user_id))
    db.commit()
    await interaction.response.send_message("🌸 춘자의 용돈 **1,000원**! 잘 써야 해!")

# --- [4] 도박 및 게임 시스템 ---

@bot.tree.command(name="배치", description="롤 티어 배치를 봅니다. (도박)")
@app_commands.describe(bet="베팅할 금액")
async def rank_game(interaction: discord.Interaction, bet: int):
    if bet < 1000: return await interaction.response.send_message("최소 1,000원부터 가능해!", ephemeral=True)
    
    cursor.execute("SELECT money FROM users WHERE id = ?", (interaction.user.id,))
    user_money = cursor.fetchone()[0]
    if user_money < bet: return await interaction.response.send_message("돈이 부족해!", ephemeral=True)

    # 확률 테이블 반영
    res = random.random()
    if res < 0.1: # 대박
        reward = bet * 5
        msg = f"💎 **다이아몬드!** 보상 {reward:,}원!"
    elif res < 0.5: # 성공
        reward = bet * 1.5
        msg = f"🟡 **골드!** 보상 {reward:,}원!"
    else: # 실패
        reward = -bet
        msg = "🟤 **아이언...** 베팅금을 잃었어."

    cursor.execute("UPDATE users SET money = money + ? WHERE id = ?", (int(reward), interaction.user.id))
    db.commit()
    await interaction.response.send_message(msg)

# --- [5] 마카롱 및 강화 ---

@bot.tree.command(name="마카롱", description="마카롱을 굽습니다 (일일 20회 제한)")
async def make_macaron(interaction: discord.Interaction):
    # 경험치에 따른 성공 확률 및 레벨 로직 생략 (기본 성공률 60%)
    if random.random() <= 0.6:
        cursor.execute("UPDATE macarons SET normal = normal + 1 WHERE user_id = ?", (interaction.user.id,))
        await interaction.response.send_message("🧁 **성공!** 맛있는 마카롱을 구웠어!")
    else:
        loss = random.randint(1000, 3000)
        cursor.execute("UPDATE users SET money = money - ? WHERE id = ?", (loss, interaction.user.id))
        await interaction.response.send_message(f"💥 **실패!** 재료비 {loss:,}원을 날렸어...")
    db.commit()

@bot.tree.command(name="강화", description="무기를 강화합니다.")
async def upgrade_weapon(interaction: discord.Interaction):
    cursor.execute("SELECT weapon_lv, money FROM users WHERE id = ?", (interaction.user.id,))
    lv, money = cursor.fetchone()
    cost = 1000 * lv
    if money < cost: return await interaction.response.send_message("돈이 부족해!", ephemeral=True)

    if random.random() < (0.9 / lv): # 레벨이 높을수록 확률 하락
        cursor.execute("UPDATE users SET weapon_lv = weapon_lv + 1, money = money - ? WHERE id = ?", (cost, interaction.user.id))
        await interaction.response.send_message(f"⚔️ **성공!** 현재 레벨: Lv.{lv+1}")
    else:
        cursor.execute("UPDATE users SET money = money - ? WHERE id = ?", (cost, interaction.user.id))
        await interaction.response.send_message("🛡️ **강화 실패...** 돈만 날렸어.")
    db.commit()

# --- [6] 실행부 (Termux) ---
if __name__ == "__main__":
    os.system('clear')
    print("==============================")
    print("🌸 춘자 봇(bot2) 통합 시스템")
    token_input = input("▶️ 봇 토큰을 입력하세요: ").strip()
    print("==============================")
    if token_input:
        bot.run(token_input)
    else:
        print("❌ 토큰 미입력.")
