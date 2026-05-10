import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import datetime
import asyncio
import os
import json

DATA_FILE = "chunza_data.json"

class ChunzaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
        self.user_data = {} 
        self.market_prices = {"일반": 1000, "슈퍼": 10000, "전설": 100000, "천상": 1000000}
        self.target_guild_id = None

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.user_data = json.load(f)
                print(f"📂 [춘자 봇] 데이터 로드 완료")
            except Exception as e: print(f"❌ 오류: {e}")

    def save_data(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"❌ 오류: {e}")

    async def setup_hook(self):
        self.load_data()
        if self.target_guild_id:
            guild = discord.Object(id=int(self.target_guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        if not self.tax_and_settlement.is_running():
            self.tax_and_settlement.start()

    @tasks.loop(time=datetime.time(hour=0, minute=0))
    async def tax_and_settlement(self):
        for user_id, data in self.user_data.items():
            money = data.get('money', 0)
            if money >= 1000000000: data['money'] *= 0.8
            elif money >= 100000000: data['money'] *= 0.9
        self.save_data()

bot = ChunzaBot()

@bot.event
async def on_ready():
    print(f"🌸 춘자 경제 봇 가동: {bot.user.name}")

@bot.tree.command(name="가입", description="경제 시스템 가입")
async def join(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in bot.user_data:
        return await interaction.response.send_message("이미 가입되어 있다도!", ephemeral=True)
    bot.user_data[user_id] = {"money": 30000, "items": {}}
    bot.save_data()
    await interaction.response.send_message(f"✨ {interaction.user.mention}님 가입 완료!")

# --- [실행 함수] ---
async def run_bot(token, target_guild_id):
    bot.target_guild_id = target_guild_id
    async with bot:
        await bot.start(token)
