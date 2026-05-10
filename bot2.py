import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import datetime
import asyncio
import os
import json

# --- [설정 및 데이터 관리] ---
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

    # [데이터 저장/불러오기 로직]
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.user_data = json.load(f)
                print(f"📂 {DATA_FILE} 데이터 로드 완료")
            except Exception as e:
                print(f"❌ 데이터 로드 오류: {e}")

    def save_data(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 데이터 저장 오류: {e}")

    async def setup_hook(self):
        self.load_data() # 시작할 때 데이터 불러오기
        await self.tree.sync()
        if not self.tax_and_settlement.is_running():
            self.tax_and_settlement.start()

    # 매일 자정 정산 및 자동 저장 루프
    @tasks.loop(time=datetime.time(hour=0, minute=0))
    async def tax_and_settlement(self):
        for user_id, data in self.user_data.items():
            if data['money'] >= 1000000000:
                data['money'] *= 0.8
            elif data['money'] >= 100000000:
                data['money'] *= 0.9
        self.save_data() # 정산 후 저장

# 봇 인스턴스 생성
bot = ChunzaBot()

# --- [메인 이벤트] ---
@bot.event
async def on_ready():
    print(f"🚀 {bot.user.name} (Bot 2) 가동 및 데이터 동기화 완료")

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # 음악 채널 반응 (예시 로직)
    guild_id = message.guild.id
    if guild_id in bot.guild_settings and message.channel.id == bot.guild_settings[guild_id].get('music_channel'):
        if not message.content.startswith('!'):
            embed = discord.Embed(title="춘자 MUSIC", description=f"🎵 **{message.content}** 곡을 재생 대기열에 추가했다도!", color=0xffc0cb)
            await message.channel.send(embed=embed)
            return

    await bot.process_commands(message)

# --- [슬래시 명령어] ---

@bot.tree.command(name="가입", description="춘자 경제 시스템에 가입합니다.")
async def join(interaction: discord.Interaction):
    user_id = str(interaction.user.id) # JSON 저장을 위해 문자열로 변환
    if user_id in bot.user_data:
        return await interaction.response.send_message("이미 가입되어 있다도!", ephemeral=True)
    
    bot.user_data[user_id] = {
        "money": 30000, "items": {"파산신청서": 5, "무기조각": 0},
        "exp": {"마카롱": 0, "알바": 0, "땅": 0},
        "level": {"마카롱": 1, "알바": 1, "땅": 1},
        "inventory": {}, "attendance": 0, "weapon_lv": 1, "durability": 100
    }
    bot.save_data() # 가입 즉시 저장
    
    embed = discord.Embed(title="🌸 춘자 경제 시스템", description=f"✨ {interaction.user.mention}님, 가입 축하금 **30,000원** 지급 완료했다도!", color=0xf4a460)
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
    
    bot.save_data() # 결과 반영 후 저장
    await interaction.response.send_message(msg)

@bot.tree.command(name="돈줘", description="지원금을 받습니다.")
async def give_money(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in bot.user_data: return await interaction.response.send_message("가입하라도!")
    
    bot.user_data[user_id]['money'] += 1000
    bot.save_data()
    await interaction.response.send_message("💰 1,000원을 지원받았다도!")

# ... (기존 클래스 및 경제 시스템 로직들) ...

# --- [실행 함수: main.py에서 호출함] ---
def run_bot(received_token, target_guild_id):
    """
    main.py에서 입력받은 토큰을 전달받아 로그인을 시도합니다.
    """
    try:
        bot.run(received_token)
    except Exception as e:
        print(f"\n❌ [춘자 봇] 로그인 중 오류 발생: {e}")
