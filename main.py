import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import os
import json
import yt_dlp
import random
from threading import Thread
from flask import Flask

# --- [1] 설정 및 데이터 로드 ---
VERSION = "v1.8.0"
AUTHOR = "CHUNZA"
CYAN, RED, GREEN, YELLOW, RESET, BOLD = "\033[96m", "\033[91m", "\033[92m", "\033[93m", "\033[0m", "\033[1m"
DATA_FILE = "server_data.json"

db = {
    "admins": [681815009466253416],
    "master_id": 731129858629042187,
    "settings": {"verify_role_name": "시민", "verify_emoji": "✅"},
    "channels": {"vote": 1501240737352646728, "suggestion": 1501199686932103199, "verify": 1501199548880650331, "music": 0},
    "active_votes": {},
    "music_queue": []
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

# --- [2] 봇 초기화 ---
os.system('clear' if os.name == 'posix' else 'cls')
print(f"{CYAN}{BOLD}>> CHUNZA PRECISION CONTROL SYSTEM <<{RESET}")
TOKEN = input(f"{CYAN}[>] BOT TOKEN: {RESET}").strip()
GUILD_ID = int(input(f"{CYAN}[>] SERVER ID: {RESET}").strip())

class ChunzaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.music_loop = False

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = ChunzaBot()

def is_auth(interaction: discord.Interaction):
    return interaction.user.id == db["master_id"] or interaction.user.id in db["admins"]

# --- [3] 음악 컨트롤러 기능 ---
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'quiet': True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

@bot.tree.command(name="음악채널설정", description="현재 채널을 음악 전용 채널로 설정합니다.")
async def set_music_ch(interaction: discord.Interaction):
    if not is_auth(interaction): return
    db["channels"]["music"] = interaction.channel_id
    save_data()
    await interaction.response.send_message("🎵 이 채널이 이제 음악 전용 채널로 지정되었습니다.")

@bot.tree.command(name="재생", description="유튜브 음악을 재생하고 컨트롤러를 생성합니다.")
async def play(interaction: discord.Interaction, 검색어: str):
    if not interaction.user.voice: return await interaction.response.send_message("🔊 음성 채널에 먼저 입장하세요!", ephemeral=True)
    await interaction.response.defer()
    
    vc = interaction.guild.voice_client or await interaction.user.voice.channel.connect()
    
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{검색어}", download=False)['entries'][0]
        url, title = info['url'], info['title']
        thumbnail = info.get('thumbnail')

    if vc.is_playing(): vc.stop()
    vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))

    embed = discord.Embed(title="🎶 현재 재생 중", description=f"**{title}**", color=0x1DB954)
    if thumbnail: embed.set_thumbnail(url=thumbnail)
    embed.add_field(name="상태", value="▶️ 재생 중", inline=True)
    embed.add_field(name="반복", value="❌ 끔", inline=True)
    embed.set_footer(text="하단 이모지로 조작: 정지 | 반복 | 섞기 | 스킵 | 일시정지")

    msg = await interaction.followup.send(embed=embed)
    # 컨트롤 이모지 추가
    control_emojis = ["⏹️", "🔁", "🔀", "⏭️", "⏸️"]
    for emoji in control_emojis: await msg.add_reaction(emoji)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    guild = bot.get_guild(payload.guild_id)
    vc = guild.voice_client
    if not vc: return

    # 음악 컨트롤러 로직
    if payload.channel_id == db["channels"]["music"] or True: # 모든 채널 허용 혹은 지정 채널 제한
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = guild.get_member(payload.user_id)
        
        if message.author.id != bot.user.id: return
        
        emoji = str(payload.emoji)
        if emoji == "⏹️": 
            await vc.disconnect()
            await channel.send("⏹️ 음악을 정지하고 나갑니다.", delete_after=5)
        elif emoji == "🔁":
            bot.music_loop = not bot.music_loop
            await channel.send(f"🔁 반복 재생이 {'활성화' if bot.music_loop else '비활성화'} 되었습니다.", delete_after=5)
        elif emoji == "🔀":
            random.shuffle(db["music_queue"])
            await channel.send("🔀 대기열이 섞였습니다.", delete_after=5)
        elif emoji == "⏭️":
            vc.stop()
            await channel.send("⏭️ 곡을 스킵했습니다.", delete_after=5)
        elif emoji == "⏸️":
            if vc.is_playing(): 
                vc.pause(); await channel.send("⏸️ 일시정지", delete_after=5)
            elif vc.is_paused(): 
                vc.resume(); await channel.send("▶️ 다시 재생", delete_after=5)
        
        await message.remove_reaction(payload.emoji, user)

# --- [4] 중복방지 익명 투표 시스템 ---
@bot.tree.command(name="투표", description="중복이 불가능한 익명 투표를 시작합니다.")
async def vote_slash(interaction: discord.Interaction, 주제: str):
    if interaction.channel_id != db["channels"]["vote"]: 
        return await interaction.response.send_message("투표 전용 채널에서 사용하세요.", ephemeral=True)
    
    embed = discord.Embed(title="🗳️ 익명 투표 (중복 불가)", description=f"**주제: {주제}**\n\n⭕: 찬성\n❌: 반대", color=0xf1c40f)
    embed.set_footer(text="투표 결과는 종료 후 마스터에게 상세 보고됩니다.")
    
    await interaction.response.send_message("투표를 게시합니다.", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("⭕")
    await msg.add_reaction("❌")
    
    db["active_votes"][str(msg.id)] = {
        "topic": 주제, 
        "voters": {}, # {user_id: choice}
        "channel": interaction.channel_id
    }
    save_data()

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot: return
    msg_id = str(reaction.message.id)
    if msg_id in db["active_votes"]:
        choice = str(reaction.emoji)
        if choice not in ["⭕", "❌"]: return
        
        vote_data = db["active_votes"][msg_id]
        
        # 중복 투표 방지
        if str(user.id) in vote_data["voters"]:
            await reaction.message.remove_reaction(reaction.emoji, user)
            return await user.send("⚠️ 이미 투표하셨습니다. 중복 투표는 불가능합니다.")
        
        # 투표 기록
        vote_data["voters"][str(user.id)] = choice
        save_data()
        
        # 본인에게만 확인 메시지
        await user.send(f"✅ '{vote_data['topic']}' 투표에 '{choice}'로 참여 완료되었습니다.")
        
        # 마스터에게 실시간 알림 (누가 무엇을 했는지)
        master = await bot.fetch_user(db["master_id"])
        await master.send(f"🔔 [투표로그] {user.name}({user.id}) 님이 '{vote_data['topic']}'에 {choice} 투표함.")
        
        # 반응 즉시 삭제 (익명성 유지)
        await reaction.message.remove_reaction(reaction.emoji, user)

@bot.tree.command(name="결과", description="마지막 투표를 종료하고 결과를 발표합니다.")
async def result_slash(interaction: discord.Interaction):
    if not is_auth(interaction): return
    if not db["active_votes"]: return await interaction.response.send_message("활성화된 투표가 없습니다.", ephemeral=True)
    
    msg_id = list(db["active_votes"].keys())[-1]
    data = db["active_votes"].pop(msg_id)
    save_data()
    
    voters = data["voters"].values()
    yes = list(voters).count("⭕")
    no = list(voters).count("❌")
    
    result_embed = discord.Embed(title="🏁 투표 종료", description=f"**주제: {data['topic']}**", color=0x2ecc71)
    result_embed.add_field(name="결과 합계", value=f"⭕ 찬성: {yes}표\n❌ 반대: {no}표", inline=False)
    result_embed.set_footer(text=f"총 투표 인원: {len(voters)}명")
    
    await interaction.response.send_message(embed=result_embed)

# --- [5] 관리 및 기타 기능 (기존 유지 및 보완) ---
@bot.tree.command(name="잠금", description="시민 권한을 잠급니다.")
async def lock(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    role = discord.utils.get(interaction.guild.roles, name=db["settings"]["verify_role_name"])
    overwrites = target.overwrites_for(role)
    overwrites.send_messages = False
    overwrites.send_messages_in_threads = False
    overwrites.create_public_threads = False
    overwrites.create_private_threads = False
    await target.set_permissions(role, overwrite=overwrites)
    await interaction.response.send_message(f"🔒 {target.mention} 잠금 완료.")

@bot.tree.command(name="해제", description="시민 권한을 해제합니다.")
async def unlock(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    role = discord.utils.get(interaction.guild.roles, name=db["settings"]["verify_role_name"])
    overwrites = target.overwrites_for(role)
    overwrites.send_messages = True
    overwrites.send_messages_in_threads = None
    overwrites.create_public_threads = None
    overwrites.create_private_threads = None
    await target.set_permissions(role, overwrite=overwrites)
    await interaction.response.send_message(f"🔓 {target.mention} 해제 완료.")

@bot.tree.command(name="청소", description="메시지를 삭제합니다.")
async def clear(interaction: discord.Interaction, 수량: int):
    if not is_auth(interaction): return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=수량)
    await interaction.followup.send(f"🧹 {len(deleted)}개의 메시지를 삭제했습니다.")

# --- [6] 서버 실행 및 Flask ---
@bot.event
async def on_ready():
    load_data()
    print(f"{GREEN}[+] CHUNZA {VERSION} ONLINE: {bot.user}{RESET}")

app = Flask('')
@app.route('/')
def home(): return "CHUNZA System Online"
def run_app(): app.run(host='0.0.0.0', port=8080)
Thread(target=run_app, daemon=True).start()

if __name__ == "__main__":
    bot.run(TOKEN)
