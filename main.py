import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import os
import sys
import json
import yt_dlp
import random
from threading import Thread
from flask import Flask

# --- [1] 기본 정보 및 컬러 설정 ---
VERSION = "v1.9.0"
AUTHOR = "CHUNZA"
CYAN, RED, GREEN, YELLOW, RESET, BOLD = "\033[96m", "\033[91m", "\033[92m", "\033[93m", "\033[0m", "\033[1m"
DATA_FILE = "server_data.json"

# --- [2] 데이터 및 음악 설정 ---
db = {
    "admins": [681815009466253416],
    "master_id": 731129858629042187,
    "settings": {"verify_role_name": "시민", "verify_emoji": "✅"},
    "channels": {
        "vote": 1501240737352646728, 
        "suggestion": 1501199686932103199, 
        "verify": 1501199548880650331,
        "music": None,
        "music_msg": None
    },
    "active_votes": {},
    "vote_logs": {} # 중복 방지용
}

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'quiet': True, 'no_warnings': True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

# 음악 상태 관리용
music_state = {"queue": [], "loop": False}

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

def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{CYAN}{BOLD}\n    ██████╗██╗  ██╗██╗   ██╗███╗   ██╗███████╗ █████╗ \n   ██╔════╝██║  ██║██║   ██║████╗  ██║╚══███╔╝██╔══██╗\n   ██║     ███████║██║   ██║██╔██╗ ██║  ███╔╝ ███████║\n   ██║     ██╔══██║██║   ██║██║╚██╗██║ ███╔╝  ██╔══██║\n   ╚██████╗██║  ██║╚██████╔╝██║ ╚████║███████╗██║  ██║\n    ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝{RESET}")
    print(f"          {YELLOW}>> PRECISION CONTROL | {VERSION} <<{RESET}")

# --- [3] 봇 클래스 설정 ---
print_banner()
TOKEN = input(f"{CYAN}[>] INPUT BOT TOKEN: {RESET}").strip()
GUILD_ID = int(input(f"{CYAN}[>] INPUT TARGET SERVER ID: {RESET}").strip())

class ChunzaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = ChunzaBot()

def is_auth(interaction: discord.Interaction):
    return interaction.user.id == db["master_id"] or interaction.user.id in db["admins"]

# --- [4] 이벤트 핸들러 (음악/심사/투표알림) ---

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # 전용 음악 채널 채팅 재생
    if message.channel.id == db["channels"].get("music"):
        await message.delete() # 입력한 채팅 삭제
        if not message.author.voice:
            return await message.channel.send(f"⚠️ {message.author.mention}님, 음성 채널에 먼저 입장하세요.", delete_after=3)
        
        query = message.content
        vc = message.guild.voice_client or await message.author.voice.channel.connect()
        
        async with message.channel.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                try:
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
                    url, title = info['url'], info['title']
                    music_state["queue"].append({"url": url, "title": title})
                except:
                    return await message.channel.send("❌ 검색 실패.", delete_after=3)

        if not vc.is_playing():
            await play_next(message.guild)
        else:
            await update_music_embed(message.guild, f"➕ 대기열 추가: {title}")

    await bot.process_commands(message)

async def play_next(guild):
    vc = guild.voice_client
    if not vc or not music_state["queue"]: return

    song = music_state["queue"].pop(0)
    def after_playing(error):
        if music_state["loop"]:
            music_state["queue"].insert(0, song)
        asyncio.run_coroutine_threadsafe(play_next(guild), bot.loop)

    vc.play(discord.FFmpegPCMAudio(song['url'], **FFMPEG_OPTIONS), after=after_playing)
    await update_music_embed(guild, f"🎵 현재 재생 중: {song['title']}")

async def update_music_embed(guild, status_text):
    ch = bot.get_channel(db["channels"]["music"])
    if not ch: return
    
    embed = discord.Embed(title="🎶 CHUNZA MUSIC PLAYER", description=status_text, color=0x00ff00)
    embed.add_field(name="명령어", value="채팅창에 제목이나 링크를 입력하면 재생됩니다.", inline=False)
    embed.set_footer(text=f"반복 재생: {'ON' if music_state['loop'] else 'OFF'}")
    
    # 기존 메시지 수정 또는 새로 생성
    try:
        msg = await ch.fetch_message(db["channels"]["music_msg"])
        await msg.edit(embed=embed)
    except:
        msg = await ch.send(embed=embed)
        db["channels"]["music_msg"] = msg.id
        save_data()
        # 이모지 순서: 정지, 반복, 섞기, 스킵, 일시정지
        for emoji in ["⏹️", "🔁", "🔀", "⏭️", "⏯️"]:
            await msg.add_reaction(emoji)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    
    # [입국 심사]
    if payload.channel_id == db["channels"]["verify"]:
        if str(payload.emoji) == db["settings"]["verify_emoji"]:
            role = discord.utils.get(guild.roles, name=db["settings"]["verify_role_name"])
            if role: await member.add_roles(role)
        return

    # [음악 컨트롤]
    if payload.channel_id == db["channels"]["music"] and payload.message_id == db["channels"]["music_msg"]:
        vc = guild.voice_client
        msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        await msg.remove_reaction(payload.emoji, member) # 반응 즉시 삭제

        if not vc: return

        emoji = str(payload.emoji)
        if emoji == "⏹️": 
            music_state["queue"] = []
            await vc.disconnect()
            await update_music_embed(guild, "⏹️ 음악이 정지되었습니다.")
        elif emoji == "🔁":
            music_state["loop"] = not music_state["loop"]
            await update_music_embed(guild, f"🔁 반복 재생 {'활성화' if music_state['loop'] else '비활성화'}")
        elif emoji == "🔀":
            random.shuffle(music_state["queue"])
            await update_music_embed(guild, "🔀 대기열이 섞였습니다.")
        elif emoji == "⏭️":
            vc.stop()
            await update_music_embed(guild, "⏭️ 다음 곡으로 넘어갑니다.")
        elif emoji == "⏯️":
            if vc.is_paused(): vc.resume(); await update_music_embed(guild, "▶️ 다시 재생합니다.")
            else: vc.pause(); await update_music_embed(guild, "⏸️ 일시 정지되었습니다.")
        return

    # [투표 알림 및 중복 금지]
    if str(payload.message_id) in db["active_votes"]:
        if str(payload.emoji) in ["⭕", "❌"]:
            vote_id = str(payload.message_id)
            if vote_id not in db["vote_logs"]: db["vote_logs"][vote_id] = []
            
            # 중복 체크
            if payload.user_id in db["vote_logs"][vote_id]:
                msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                await msg.remove_reaction(payload.emoji, member)
                return
            
            db["vote_logs"][vote_id].append(payload.user_id)
            save_data()
            
            # 마스터에게 알림
            master = await bot.fetch_user(db["master_id"])
            topic = db["active_votes"][vote_id]["topic"]
            await master.send(f"🗳️ **[투표 알림]**\n유저: {member} ({member.id})\n항목: {payload.emoji}\n주제: {topic}")

# --- [5] 전용 슬래시 명령어 ---

@bot.tree.command(name="음악", description="음악 전용 채널을 설정합니다.")
async def set_music_channel(interaction: discord.Interaction, 채널: discord.TextChannel):
    if not is_auth(interaction): return
    db["channels"]["music"] = 채널.id
    db["channels"]["music_msg"] = None
    save_data()
    await update_music_embed(interaction.guild, "🎶 음악 재생 준비 완료")
    await interaction.response.send_message(f"✅ {채널.mention}이 음악 전용 채널로 설정되었습니다.")

@bot.tree.command(name="권한부여", description="새로운 관리자를 등록합니다.")
async def auth_add(interaction: discord.Interaction, 유저: discord.Member):
    if interaction.user.id != db["master_id"]: return await interaction.response.send_message("마스터 전용 권한입니다.", ephemeral=True)
    if 유저.id not in db["admins"]:
        db["admins"].append(유저.id); save_data()
        await interaction.response.send_message(f"✅ {유저.mention} 님이 관리자로 등록되었습니다.")
    else: await interaction.response.send_message("이미 관리자입니다.", ephemeral=True)

@bot.tree.command(name="권한해제", description="관리자 권한을 회수합니다.")
async def auth_remove(interaction: discord.Interaction, 유저: discord.Member):
    if interaction.user.id != db["master_id"]: return await interaction.response.send_message("마스터 전용 권한입니다.", ephemeral=True)
    if 유저.id in db["admins"]:
        db["admins"].remove(유저.id); save_data()
        await interaction.response.send_message(f"❌ {유저.mention} 님의 권한이 해제되었습니다.")
    else: await interaction.response.send_message("등록된 관리자가 아닙니다.", ephemeral=True)

@bot.tree.command(name="잠금", description="시민 역할의 채팅 권한을 차단합니다.")
async def lock_slash(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    role = discord.utils.get(interaction.guild.roles, name=db["settings"]["verify_role_name"])
    if not role: return await interaction.response.send_message("역할을 찾을 수 없습니다.", ephemeral=True)
    overwrites = target.overwrites_for(role)
    overwrites.send_messages = False
    overwrites.send_messages_in_threads = False
    overwrites.create_public_threads = False
    overwrites.create_private_threads = False
    await target.set_permissions(role, overwrite=overwrites)
    await interaction.response.send_message(f"🔒 {target.mention} 잠금 완료.")

@bot.tree.command(name="해제", description="시민 역할의 채팅 권한을 해제합니다.")
async def unlock_slash(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    role = discord.utils.get(interaction.guild.roles, name=db["settings"]["verify_role_name"])
    if not role: return await interaction.response.send_message("역할을 찾을 수 없습니다.", ephemeral=True)
    overwrites = target.overwrites_for(role)
    overwrites.send_messages = True
    await target.set_permissions(role, overwrite=overwrites)
    await interaction.response.send_message(f"🔓 {target.mention} 해제 완료.")

@bot.tree.command(name="투표", description="익명 투표 시작 (중복 금지)")
async def vote_slash(interaction: discord.Interaction, 주제: str):
    if interaction.channel_id != db["channels"]["vote"]: return await interaction.response.send_message("투표 채널 전용입니다.", ephemeral=True)
    embed = discord.Embed(title="🗳️ 익명 투표", description=f"**{주제}**\n\n⭕: 찬성 | ❌: 반대\n(한 번만 투표 가능)", color=0xf1c40f)
    await interaction.response.send_message("투표를 시작합니다.", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("⭕"); await msg.add_reaction("❌")
    db["active_votes"][str(msg.id)] = {"topic": 주제, "channel": interaction.channel_id}
    save_data()

@bot.tree.command(name="결과", description="투표 종료 및 결과 확인")
async def result_slash(interaction: discord.Interaction):
    if not is_auth(interaction): return
    if not db["active_votes"]: return await interaction.response.send_message("진행 중인 투표가 없습니다.", ephemeral=True)
    msg_id = list(db["active_votes"].keys())[-1]
    data = db["active_votes"].pop(msg_id)
    if msg_id in db["vote_logs"]: db["vote_logs"].pop(msg_id)
    
    ch = bot.get_channel(data["channel"])
    try:
        msg = await ch.fetch_message(int(msg_id))
        results = {str(r.emoji): r.count - 1 for r in msg.reactions if str(r.emoji) in ["⭕", "❌"]}
        await interaction.response.send_message(f"🏁 **최종 결과**\n주제: {data['topic']}\n⭕: {results.get('⭕',0)} | ❌: {results.get('❌',0)}")
        await msg.delete()
        save_data()
    except:
        await interaction.response.send_message("메시지를 찾을 수 없습니다.")

@bot.tree.command(name="청소", description="메시지 청소")
async def clear_slash(interaction: discord.Interaction, 수량: int):
    if not is_auth(interaction): return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=수량)
    await interaction.followup.send(f"🧹 {len(deleted)}개 삭제 완료.")

@bot.tree.command(name="명령어", description="명령어 목록 확인")
async def help_slash(interaction: discord.Interaction):
    embed = discord.Embed(title=f"🛡️ {AUTHOR} {VERSION} CONTROL", color=0x3498db)
    embed.add_field(name="🎶 Music", value="`/음악` (채널 지정 후 채팅으로 재생)", inline=True)
    embed.add_field(name="🗳️ Vote", value="`/투표`, `/결과`", inline=True)
    embed.add_field(name="🛡️ Admin", value="`/청소`, `/잠금`, `/해제`, `/권한부여`, `/권한해제`, `/백업`, `/복구`", inline=False)
    await interaction.response.send_message(embed=embed)

# --- [나머지 기본 명령어 유지] ---
@bot.tree.command(name="문의", description="개발자 건의")
async def contact_slash(interaction: discord.Interaction, 내용: str):
    master = await bot.fetch_user(db["master_id"])
    await master.send(f"📩 [{interaction.user}] 문의: {내용}")
    await interaction.response.send_message("✅ 전달 완료.", ephemeral=True)

@bot.tree.command(name="현황", description="서버 인원")
async def status_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"📊 인원: **{interaction.guild.member_count}명**")

@bot.tree.command(name="백업", description="데이터 백업")
async def backup_slash(interaction: discord.Interaction):
    if not is_auth(interaction): return
    save_data(); await interaction.response.send_message("💾 백업 완료.")

@bot.tree.command(name="복구", description="데이터 복구")
async def restore_slash(interaction: discord.Interaction):
    if not is_auth(interaction): return
    load_data(); await interaction.response.send_message("🛠️ 복구 완료.")

@bot.tree.command(name="생성", description="채널 생성")
async def create_slash(interaction: discord.Interaction, 카테고리id: str, 이름: str):
    if not is_auth(interaction): return
    cat = bot.get_channel(int(카테고리id))
    new_ch = await interaction.guild.create_text_channel(이름, category=cat)
    await interaction.response.send_message(f"📂 {new_ch.mention} 생성.")

@bot.tree.command(name="추방", description="유저 추방")
async def kick_slash(interaction: discord.Interaction, 유저: discord.Member):
    if not is_auth(interaction): return
    await 유저.kick(); await interaction.response.send_message(f"👢 {유저.display_name} 추방.")

@bot.tree.command(name="차단", description="유저 차단")
async def ban_slash(interaction: discord.Interaction, 유저: discord.Member):
    if not is_auth(interaction): return
    await 유저.ban(); await interaction.response.send_message(f"🔨 {유저.display_name} 차단.")

@bot.tree.command(name="삭제", description="채널 삭제")
async def delete_slash(interaction: discord.Interaction, 채널: discord.TextChannel = None):
    if not is_auth(interaction): return
    target = 채널 or interaction.channel
    await target.delete(); await interaction.response.send_message("삭제됨.", ephemeral=True)

# --- [7] 서버 실행 ---
@bot.event
async def on_ready():
    load_data(); print_banner()
    print(f"{GREEN}[+] CHUNZA {VERSION} ONLINE: {bot.user}{RESET}")

app = Flask('')
@app.route('/')
def home(): return "CHUNZA v1.9.0 Online"
def run_app(): app.run(host='0.0.0.0', port=8080)
Thread(target=run_app, daemon=True).start()

if __name__ == "__main__":
    bot.run(TOKEN)
