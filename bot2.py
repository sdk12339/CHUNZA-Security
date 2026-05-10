import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import datetime
import asyncio
import os

# --- [설정 및 데이터베이스 대용] ---
class ChunzaBot(commands.Bot):
    def __init__(self):
        # Termux 환경 및 봇2 특성에 맞춘 인텐트 설정
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
        self.user_data = {} # 유저 경제 데이터
        self.market_prices = {"일반": 1000, "슈퍼": 10000, "전설": 100000, "천상": 1000000}
        self.guild_settings = {} # 서버별 설정

    async def setup_hook(self):
        # 슬래시 명령어 동기화 (처음 실행 시 서버 반영에 시간이 걸릴 수 있음)
        await self.tree.sync()
        if not self.tax_and_settlement.is_running():
            self.tax_and_settlement.start()

    # 매일 자정 정산 및 세금 부과 루프
    @tasks.loop(time=datetime.time(hour=0, minute=0))
    async def tax_and_settlement(self):
        for user_id, data in self.user_data.items():
            if data['money'] >= 1000000000: # 10억 이상 세금 20%
                data['money'] *= 0.8
            elif data['money'] >= 100000000: # 1억 이상 세금 10%
                data['money'] *= 0.9

# 봇 인스턴스 생성
bot = ChunzaBot()

# --- [1. 음악 시스템 응답 로직] ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    guild_id = message.guild.id
    # 음악 채널 설정이 되어 있고, 해당 채널에 채팅이 올라오면 반응
    if guild_id in bot.guild_settings and message.channel.id == bot.guild_settings[guild_id].get('music_channel'):
        if not message.content.startswith('!'):
            embed = discord.Embed(title="춘자 MUSIC", description=f"🎵 **{message.content}** 곡을 재생 대기열에 추가했다도!", color=0xffc0cb)
            msg = await message.channel.send(embed=embed)
            emojis = ['⏹️', '🔁', '📜', '🔀', '⏭️', '⏸️']
            for emoji in emojis: await msg.add_reaction(emoji)
            return

    await bot.process_commands(message)

# --- [2. 슬래시 명령어 (가입/경제/노동)] ---

@bot.tree.command(name="가입", description="춘자 경제 시스템에 가입합니다.")
async def join(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in bot.user_data:
        return await interaction.response.send_message("이미 가입되어 있다도!", ephemeral=True)
    
    bot.user_data[user_id] = {
        "money": 30000, "items": {"파산신청서": 5, "무기조각": 0},
        "exp": {"마카롱": 0, "알바": 0, "땅": 0},
        "level": {"마카롱": 1, "알바": 1, "땅": 1},
        "inventory": {}, "attendance": 0, "weapon_lv": 1, "durability": 100
    }
    
    embed = discord.Embed(title="🌸 춘자 경제 시스템", description=f"✨ {interaction.user.mention}님, 환영한다도!\n가입 축하금 **30,000원**과 **파산신청서 5장**을 지급했다도!", color=0xf4a460)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="마카롱", description="마카롱 베이킹을 시작합니다.")
async def macaron(interaction: discord.Interaction):
    if interaction.user.id not in bot.user_data:
        return await interaction.response.send_message("`!가입`을 먼저 하라도!", ephemeral=True)
        
    success = random.random() < 0.6
    if success:
        res = random.choices(["일반", "슈퍼", "전설", "천상"], weights=[95, 4.5, 0.49, 0.01])[0]
        bot.user_data[interaction.user.id]['money'] += bot.market_prices[res]
        await interaction.response.send_message(f"🧁 **{res}** 마카롱 구워내기 성공! {bot.market_prices[res]:,}원을 벌었다도!")
    else:
        loss = random.randint(1000, 2000)
        bot.user_data[interaction.user.id]['money'] -= loss
        await interaction.response.send_message(f"🔥 마카롱을 태워먹었다도... {loss:,}원을 잃었다도.")

@bot.tree.command(name="돈줘", description="지원금을 받습니다.")
async def give_money(interaction: discord.Interaction):
    if interaction.user.id not in bot.user_data:
        return await interaction.response.send_message("가입부터 하라도!", ephemeral=True)
    bot.user_data[interaction.user.id]['money'] += 1000
    await interaction.response.send_message("💰 1,000원을 지원받았다도! 나중에 또 오라도.")

@bot.tree.command(name="춘자", description="봇 상태 확인")
async def bot_info(interaction: discord.Interaction):
    status = f"작동 상태: 정상\n핑: {round(bot.latency * 1000)}ms\n언어: Python(discord.py)"
    await interaction.response.send_message(f"🤖 **춘자 정보**\n```{status}```")

# --- [3. 실행 함수 (main.py 호출용)] ---
def run_bot():
    # 여기에 봇 2번의 토큰을 직접 입력하세요
    MY_TOKEN = "여기에_봇2_토큰_입력"
    if MY_TOKEN == "여기에_봇2_토큰_입력":
        print("❌ 오류: bot2.py에 토큰이 입력되지 않았습니다.")
        return
    bot.run(MTUwMDM4Nzc4ODU5NDM1MjE2OA.GtGeCO.E-G1OYGIsukJOwZQANeMQHMW6gzuoAAiBZ6cFo)
