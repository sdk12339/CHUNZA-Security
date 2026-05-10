import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
import asyncio

# --- 초기 설정 ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class DodoBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 여기서 슬래시 커맨드를 동기화합니다.
        await self.tree.sync()

bot = DodoBot()

# --- 데이터베이스 대용 (실제 서비스 시 DB 연동 필수) ---
# 예시: user_data = {user_id: {"money": 30000, "exp_macaron": 0, "lv_weapon": 1, ...}}
user_data = {}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "money": 0,
            "bankrupt_papers": 0,
            "check_in_count": 0,
            "exp_macaron": 0,
            "exp_job": 0,
            "exp_dig": 0,
            "lv_weapon": 1,
            "weapon_durability": 100,
            "weapon_pieces": 0,
            "macarons": {"일반": 0, "슈퍼": 0, "전설": 0, "천상": 0},
            "last_donju": None,
            "last_checkin": None,
            "daily_job_count": 0,
            "daily_macaron_count": 0,
            "daily_dig_count": 0,
            "stars": 0,
            "last_disaster": None,
            "saving_plan": None,
            "saving_money": 0,
            "saving_start_date": None,
            "transfer_count": 0,
            "skin": {"profile_border": None, "bg_border": None, "name_color": None, "neon": False, "bg_image": None}
        }
    return user_data[user_id]

# --- 1. 가입 및 기본 명령어 ---

@bot.tree.command(name="도움말", description="도도 봇의 간단한 설명을 확인합니다.")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 도도 봇 도움말", description="`/가입` 명령어로 시작하세요!", color=0xffd700)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="가입", description="도도 봇을 시작하기 위해 가입합니다.")
async def join_cmd(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if user["money"] > 0 or user["check_in_count"] > 0:
        await interaction.response.send_message("이미 가입되어 있다도! 🐥")
        return
    
    user["money"] = 30000
    user["bankrupt_papers"] = 5
    await interaction.response.send_message(f"{interaction.user.mention}님, 환영한다도! 가입 축하금 **30,000원**과 **파산신청서🔖 5장**을 지급했다도! 가방에서 확인해봐!")

# --- 2. 돈 획득 명령어 ---

@bot.tree.command(name="돈줘", description="10분에 한 번 돈을 받습니다.")
async def get_money(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    now = datetime.datetime.now()
    
    if user["last_donju"] and (now - user["last_donju"]).total_seconds() < 600:
        await interaction.response.send_message("아직 10분이 안 지났다도! 좀만 기다려달라도.", ephemeral=True)
        return

    reward = 1000
    msg = "꾸준히 모으는 게 중요하다도! 1,000원 지급 완료!"
    
    if user["last_donju"] is None:
        reward = 30000
        user["bankrupt_papers"] += 5
        msg = "처음으로 `/돈줘`를 입력했구나! 30,000원과 파산신청서 5장을 선물로 줬다도! 🎁"
    
    user["money"] += reward
    user["last_donju"] = now
    await interaction. Gallagher.send_message(msg)

@bot.tree.command(name="출석체크", description="하루에 한 번 출석체크를 합니다.")
async def check_in(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    # 출석 체크 로직 (날짜 비교 생략)
    user["check_in_count"] += 1
    user["money"] += 10000
    
    bonus_msg = ""
    milestones = {5: 100000, 10: 300000, 30: 3000000, 50: 10000000, 100: 30000000, 200: 50000000, 300: 70000000, 400: 90000000, 500: 100000000, 1000: 300000000}
    if user["check_in_count"] in milestones:
        bonus = milestones[user["check_in_count"]]
        user["money"] += bonus
        bonus_msg = f"\n🎊 대박! {user['check_in_count']}일 달성 보너스로 **{bonus:,}원**을 더 줬다도!"
        
    await interaction.response.send_message(f"오늘도 와줬구나! 10,000원 지급 완료! (누적 {user['check_in_count']}일){bonus_msg}")

# --- 3. 마카롱 시스템 ---

@bot.tree.command(name="마카롱", description="마카롱을 구워 돈과 경험치를 얻습니다.")
async def bake_macaron(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if user["daily_macaron_count"] >= 20:
        await interaction.response.send_message("오늘은 더 이상 마카롱을 구울 수 없다도! (일일 20회 제한)", ephemeral=True)
        return
    
    # 레벨별 확률 로직 (사용자가 준 테이블 적용)
    # 기본 레벨 1 기준 예시
    success = random.random() < 0.6
    if success:
        kind_rand = random.random() * 100
        if kind_rand < 60: kind, count, exp = "일반", 1, 1
        elif kind_rand < 85: kind, count, exp = "일반", 3, 2
        elif kind_rand < 95: kind, count, exp = "일반", 5, 3
        elif kind_rand < 99.5: kind, count, exp = "슈퍼", 1, 5
        elif kind_rand < 99.99: kind, count, exp = "전설", 1, 20
        else: kind, count, exp = "천상", 1, 100
        
        user["macarons"][kind] += count
        user["exp_macaron"] += exp
        user["daily_macaron_count"] += 1
        await interaction.response.send_message(f"🍭 따끈따끈한 **{kind} 마카롱**을 {count}개 구웠다도! (경험치 +{exp})")
    else:
        loss = random.randint(1000, 2000)
        user["money"] -= loss
        user["daily_macaron_count"] += 1
        await interaction.response.send_message(f"😰 아차차! 마카롱을 태워먹었다도... 재료비 **{loss:,}원**을 날렸다도.")

@bot.tree.command(name="마카롱시세", description="마카롱 시세를 확인합니다.")
async def macaron_price(interaction: discord.Interaction):
    # 시세 변동 로직 (랜덤)
    prices = {"일반": random.randint(500, 5000), "슈퍼": random.randint(10000, 50000), "전설": random.randint(500000, 2000000), "천상": random.randint(10000000, 50000000)}
    embed = discord.Embed(title="📈 마카롱 오늘의 시세", color=0xff69b4)
    for k, v in prices.items():
        embed.add_field(name=f"{k} 마카롱", value=f"{v:,}원", inline=False)
    await interaction.response.send_message(embed=embed)

# --- 4. 알바 시스템 ---

@bot.tree.command(name="알바", description="아르바이트를 하러 떠납니다.")
async def working(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if user["daily_job_count"] >= 50:
        await interaction.response.send_message("오늘은 너무 열심히 일했다도! 내일 다시 하자도. (50회 제한)")
        return
    
    # 30초 쿨타임 및 성공 확률 로직 적용 필요
    res = random.random()
    if res < 0.7: # 성공 (레벨 1 기준)
        jobs = [("지갑 줍기", 0.01), ("과외", 0.09), ("옷가게", 0.25), ("편의점", 0.25), ("폐지 줍기", 0.2), ("봉사 활동", 0.2)]
        # 가중치 랜덤 선택 로직...
        job_name = "편의점" 
        pay = random.randint(8000, 12000)
        user["money"] += pay
        user["exp_job"] += 1
        await interaction.response.send_message(f"💼 **{job_name}** 알바 성공! 시급으로 **{pay:,}원**을 받았다도!")
    else:
        user["exp_job"] -= 2
        await interaction.response.send_message("🤕 알바하다가 실수를 해서 혼났다도... 경험치가 깎였다도.")

# --- 5. 땅파기 시스템 ---

@bot.tree.command(name="땅파기", description="밖으로 나가 땅을 파봅니다.")
async def digging(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if user["daily_dig_count"] >= 200:
        await interaction.response.send_message("땅을 너무 많이 파서 이제 구멍이 없다도!")
        return

    res = random.random()
    if res < 0.05: # 유물 발견 (5% 고정)
        relic_price = random.randint(20000, 100000000)
        user["money"] += relic_price
        user["exp_dig"] += 10
        await interaction.response.send_message(f"💛 우와! 유물을 발견했다도! 가치가 무려 **{relic_price:,}원**이라도!")
    elif res < 0.95: # 성공
        gain = random.randint(10, 500)
        user["money"] += gain
        user["exp_dig"] += 1
        await interaction.response.send_message(f"🔹 땅을 파서 **{gain}원**을 찾았다도! 진짜 나오네?")
    else: # 실패
        loss = random.randint(1000, 5000)
        user["money"] -= loss
        user["exp_dig"] -= 10
        await interaction.response.send_message(f"🔸 아야! 땅 파다가 돌부리에 걸려 넘어졌다도. 병원비로 **{loss:,}원** 썼다도.")

# --- 6. 미니게임 (배치, 발로, 마크, 소개팅, 수능) ---

@bot.tree.command(name="배치", description="롤 티어 배치를 봅니다.")
@app_commands.describe(bet="베팅할 금액")
async def lol_rank(interaction: discord.Interaction, bet: int):
    if bet < 1000: return await interaction.response.send_message("최소 1,000원 이상 베팅해야 한다도!")
    user = get_user(interaction.user.id)
    if user["money"] < bet: return await interaction.response.send_message("돈이 부족하다도!")

    # 확률 테이블 적용
    rand = random.random() * 100
    if rand < 0.02: tier, mult = "챌린저 👑", 100
    elif rand < 0.06: tier, mult = "그랜드마스터 🔴", 50
    elif rand < 0.4: tier, mult = "마스터 🟣", 20
    elif rand < 3.0: tier, mult = "다이아몬드 💎", 5
    elif rand < 8.0: tier, mult = "에메럴드 💚", 3
    elif rand < 17.5: tier, mult = "플래티넘 💍", 2
    elif rand < 45.5: tier, mult = "골드 🟡", 1
    elif rand < 75.5: tier, mult = "실버 ⚪", -1
    elif rand < 95.5: tier, mult = "브론즈 🟤", -2
    else: tier, mult = "아이언 🔘", -5

    result = bet * mult
    user["money"] += result
    await interaction.response.send_message(f"🎮 배치 결과... 당신은 **{tier}**! 보상으로 **{result:,}원**이 변동되었다도!")

# --- 7. 강화 및 공격 시스템 ---

@bot.tree.command(name="강화", description="무기를 강화합니다.")
async def upgrade_weapon(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    lv = user["lv_weapon"]
    cost = 1000 # 원래는 레벨별 비용 테이블 적용
    
    if user["money"] < cost: return await interaction.response.send_message("강화 비용이 부족하다도!")
    
    user["money"] -= cost
    success_rate = 1.0 - (lv * 0.01) # 간단한 예시 확률
    if random.random() < success_rate:
        user["lv_weapon"] += 1
        user["weapon_durability"] = 100
        await interaction.response.send_message(f"🗡️ 강화 성공! 무기 레벨이 **Lv.{user['lv_weapon']}**가 되었다도!")
    else:
        # 실패 및 파괴 로직...
        await interaction.response.send_message("💥 강화 실패! 무기가 손상되었다도.")

@bot.tree.command(name="공격", description="던전에 입장하여 보상을 얻습니다.")
async def attack_dungeon(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    # 던전 선택 로직 및 레벨 제한 체크...
    # 해변 🏖️, 신사 ⛩️, 타워 🗼, 성 🏰
    await interaction.response.send_message("어떤 던전에 입장하겠냐도? (로직에 따라 구현 예정)")

# --- 8. 상점 및 가방 ---

@bot.tree.command(name="상점", description="상점을 엽니다.")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🏪 도도 상점", description="다양한 물건을 팔고 있다도!")
    embed.add_field(name="1. 랜덤박스 소형 📦", value="5,000,000원", inline=True)
    embed.add_field(name="2. 랜덤박스 대형 🎁", value="10,000,000원", inline=True)
    embed.add_field(name="3. 무기 구매 🗡️", value="/상점 명령어 내부 확인", inline=False)
    embed.add_field(name="4. 환생(별) ⭐", value="200,000,000원", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="가방", description="보유 아이템을 확인하고 사용합니다.")
async def inventory(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    await interaction.response.send_message(f"🎒 가방을 열었다도! 파산신청서: {user['bankrupt_papers']}장 등...", ephemeral=True)

# --- 9. 기타 기능 (송금, 순위, 정보, 밀항 등) ---

@bot.tree.command(name="송금", description="다른 유저에게 돈을 보냅니다.")
@app_commands.describe(member="받을 유저", amount="보낼 금액")
async def transfer(interaction: discord.Interaction, member: discord.Member, amount: int):
    sender = get_user(interaction.user.id)
    receiver = get_user(member.id)
    
    fee = int(amount * 0.1)
    total = amount + fee
    
    if sender["money"] < total: return await interaction.response.send_message("수수료 포함 잔액이 부족하다도!")
    if amount > 5000000: return await interaction.response.send_message("일반 송금은 500만원까지만 가능하다도!")
    
    sender["money"] -= total
    receiver["money"] += amount
    await interaction.response.send_message(f"💸 {member.mention}님께 {amount:,}원을 보냈다도! (수수료 {fee:,}원 차감)")

@bot.tree.command(name="정보", description="나의 상세 정보를 확인합니다.")
async def info(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    embed = discord.Embed(title=f"👤 {interaction.user.name}의 정보", color=0x00ff00)
    embed.add_field(name="💰 잔액", value=f"{user['money']:,}원")
    embed.add_field(name="⭐ 별(환생)", value=f"{user['stars']}개")
    embed.add_field(name="🗡️ 무기 레벨", value=f"Lv.{user['lv_weapon']} (내구도: {user['weapon_durability']})")
    # 마카롱 개수 등 추가...
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="밀항", description="익명의 누군가에게 돈을 보냅니다.")
async def smuggling(interaction: discord.Interaction, amount: int, message: str = None):
    # 밀항 로직 구현...
    await interaction.response.send_message("🚢 누군가에게 배를 띄웠다도! 잘 도착하길 빌라도.")

# --- 10. 서버장 및 관리자 명령어 ---

@bot.tree.command(name="돈받기", description="관리자 전용: 돈을 생성합니다.")
@commands.has_permissions(administrator=True)
async def admin_get_money(interaction: discord.Interaction, amount: int):
    user = get_user(interaction.user.id)
    user["money"] += amount
    await interaction.response.send_message(f"👑 관리자 권한으로 {amount:,}원을 생성했다도!")

# 봇 실행
bot.run("YOUR_BOT_TOKEN")
