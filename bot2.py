import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import datetime
import asyncio
import os
import json

# --- [1] 설정 및 데이터 관리 ---
DATA_FILE = "chunza_data.json"

class ChunzaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
        self.user_data = {} 
        self.market_prices = {"일반": 1000, "슈퍼": 10000, "전설": 100000, "천상": 1000000}
        self.guild_settings = {} 
        self.target_guild_id = None # main.py에서 전달받을 서버 ID

    # 데이터 불러오기
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.user_data = json.load(f)
                print(f"📂 [춘자 봇] {DATA_FILE} 데이터 로드 완료")
            except Exception as e:
                print(f"❌ 데이터 로드 오류: {e}")

    # 데이터 저장
    def save_data(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"❌ 데이터 저장 오류: {e}")

    # 명령어 동기화 및 루프 시작
    async def setup_hook(self):
        self.load_data()
        
        # 특정 서버 ID가 입력되었다면 해당 서버에만 즉시 동기화
        if self.target_guild_id:
            try:
                guild = discord.Object(id=int(self.target_guild_id))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"✅ [춘자 봇] 서버({self.target_guild_id}) 명령어 동기화 완료!")
            except Exception as e:
                print(f"⚠️ [춘자 봇] 동기화 중 오류: {e}")
        else:
            await self.tree.sync()
            print("✅ [춘자 봇] 전체 명령어 동기화 완료!")

        # 정산 루프 시작
        if not self.tax_and_settlement.is_running():
            self.tax_and_settlement.start()

    # 매일 자정 정산 루프
    @tasks.loop(time=datetime.time(hour=0, minute=0))
    async def tax_and_settlement(self):
        for user_id, data in self.user_data.items():
            if data.get('money', 0) >= 1000000000:
                data['money'] *= 0.8
            elif data.get('money', 0) >= 100000000:
                data['money'] *= 0.9
        self.save_data()
        print("💰 [춘자 봇] 자정 세금 정산 완료!")

bot = ChunzaBot()

# --- [2] 실행 함수 (main.py에서 호출) ---
async def run_bot(token, target_guild_id):
    bot.target_guild_id = target_guild_id
    async with bot:
        # 절대 bot.run()을 쓰지 마세요. main.py의 asyncio와 충돌합니다.
        await bot.start(token)

# --- [3] 이벤트 및 명령어 ---
@bot.event
async def on_ready():
    print(f"==============================")
    print(f"🌸 춘자 경제 봇 가동: {bot.user.name}")
    print(f"==============================")

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

# --- [4] 슬래시 명령어들 ---

@bot.tree.command(name="가입", description="춘자 경제 시스템에 가입합니다.")
async def join(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in bot.user_data:
        return await interaction.response.send_message("이미 가입되어 있다도!", ephemeral=True)
    
    bot.user_data[user_id] = {
        "money": 30000, 
        "items": {"파산신청서": 5, "무기조각": 0},
        "exp": {"마카롱": 0, "알바": 0, "땅": 0},
        "level": {"마카롱": 1, "알바": 1, "땅": 1},
        "inventory": {}, "attendance": 0, "weapon_lv": 1, "durability": 100
    }
    bot.save_data()
    
    embed = discord.Embed(title="🌸 춘자 경제 시스템", description=f"✨ {interaction.user.mention}님, 가입 축하금 **30,000원** 지급 완료!", color=0xf4a460)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="마카롱", description="마카롱 베이킹을 시작합니다.")
async def macaron(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in bot.user_data:
        return await interaction.response.send_message("`!가입`부터 하라도!", ephemeral=True)
        
    success = random.random() < 0.6
    if success:
        res = random.choices(["일반", "슈퍼", "전설", "천상"], weights=[95, 4.5, 0.49, 0.01])[0]
        bot.user_data[user_id]['money'] += bot.market_prices[res]
        msg = f"🧁 **{res}** 마카롱 성공! {bot.market_prices[res]:,}원을 벌었다도!"
    else:
        loss = random.randint(1000, 2000)
        bot.user_data[user_id]['money'] -= loss
        msg = f"🔥 마카롱을 태웠다도... {loss:,}원을 잃었다도."
    
    bot.save_data()
    await interaction.response.send_message(msg)

@bot.tree.command(name="돈줘", description="지원금을 받습니다.")
async def give_money(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in bot.user_data: 
        return await interaction.response.send_message("가입하라도!", ephemeral=True)
    
    bot.user_data[user_id]['money'] += 1000
    bot.save_data()
    await interaction.response.send_message("💰 1,000원을 지원받았다도!")
