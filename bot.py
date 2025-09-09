import os
import re
import discord
from discord.ext import commands

# ✅ 최소 인텐트: 꼭 필요한 것만
intents = discord.Intents.default()
intents.message_content = True   # 개발자 포털에서도 ON 필요
intents.members = True           # 닉네임 변경 대상 확인용

bot = commands.Bot(command_prefix="!", intents=intents)

def extract_prefix_only(nickname):
    prefix = ""
    bracket_patterns = [
        r'\[[^\]]+\]', r'꒰[^꒱]+꒱', r'【[^】]+】', r'「[^」]+」', r'《[^》]+》',
    ]
    combined_pattern = re.compile(r'^(' + '|'.join(bracket_patterns) + r')\s*')
    while True:
        match = combined_pattern.match(nickname)
        if match:
            prefix += match.group(0)
            nickname = nickname[match.end():]
        else:
            break
    if prefix and not prefix.endswith(' '):
        prefix += ' '
    special_pattern = re.compile(r'^[#*!~]+')
    match = special_pattern.match(nickname)
    if match:
        cleaned = ""
        for c in match.group(0):
            if c not in cleaned:
                cleaned += c
        if cleaned:
            prefix += cleaned + ' '
    return prefix

# ✅ (선택) 환경변수로 제한을 주고 싶으면: "guildId1,guildId2" 형태
ALLOWED_GUILDS = set(map(int, os.getenv("ALLOWED_GUILDS","").split(","))) if os.getenv("ALLOWED_GUILDS") else None
ALLOWED_CHANNELS = set(map(int, os.getenv("ALLOWED_CHANNELS","").split(","))) if os.getenv("ALLOWED_CHANNELS") else None

def is_allowed(message: discord.Message) -> bool:
    if not message.guild:
        return False
    if ALLOWED_GUILDS and message.guild.id not in ALLOWED_GUILDS:
        return False
    if ALLOWED_CHANNELS and message.channel.id not in ALLOWED_CHANNELS:
        return False
    return True

@bot.event
async def on_ready():
    print(f"✅ 로그인 성공: {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if not is_allowed(message):
        return

    new_name = message.content.strip()
    current_nick = message.author.display_name
    prefix = extract_prefix_only(current_nick)

    if new_name == "삭제":
        new_nickname = prefix.strip()
    else:
        new_nickname = f"{prefix}{new_name}"

    if new_nickname != current_nick:
        try:
            await message.author.edit(nick=new_nickname)
            print(f"🎉 닉네임 변경: {current_nick} → {new_nickname}")
        except discord.Forbidden:
            print("❌ 권한 부족(Manage Nicknames / 역할 순서 확인)")
        except discord.HTTPException as e:
            print(f"⚠️ HTTP 오류: {e}")

    await bot.process_commands(message)

# 🔒 토큰은 무조건 환경변수에서!
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN 환경변수가 없습니다.")
else:
    print("🔑 토큰 로드 성공, 길이:", len(TOKEN))

try:
    bot.run(TOKEN)
except Exception as e:
    print(f"🚨 봇 실행 중 오류 발생: {e}")
