import discord
from discord.ext import commands
import re
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ 로그인 성공: {bot.user}")

def extract_prefix_only(nickname):
    prefix = ""

    # 다양한 괄호형 접두사
    bracket_patterns = [
        r'\[[^\]]+\]',
        r'꒰[^꒱]+꒱',
        r'【[^】]+】',
        r'「[^」]+」',
        r'《[^》]+》',
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

    # 연속 특수문자 처리 (#, *, !, ~ 등)
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

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print(f"📩 메시지 감지됨: {message.content} (채널: {message.channel.id}, 서버: {message.guild.id if message.guild else 'DM'})")

    # 여러 서버/채널 대응 가능하게 딕셔너리 형태로 관리
    allowed_channels = {
        1369681601856012399: [1414591898366251038],  # 서버 1: 허용 채널들
        # 다른 서버도 필요하면 추가 가능
    }

    # 길드가 없거나 해당 서버에 등록된 채널이 아님
    if not message.guild or message.guild.id not in allowed_channels:
        return
    if message.channel.id not in allowed_channels[message.guild.id]:
        return

    print("✅ 허용된 채널에서 메시지 감지됨")

    new_name = message.content.strip()
    current_nick = message.author.display_name
    prefix = extract_prefix_only(current_nick)

    # "삭제" 입력 시 접두사 + 특수문자만 남기기
    if new_name == "삭제":
        new_nickname = prefix.strip()
    else:
        new_nickname = f"{prefix}{new_name}"

    print(f"🔄 닉네임 변경 시도: {current_nick} → {new_nickname}")

    if new_nickname != current_nick:
        try:
            await message.author.edit(nick=new_nickname)
            print(f"🎉 닉네임 변경 성공: {message.author} → {new_nickname}")
            # 필요하면 강제 재적용
            # await asyncio.sleep(1)
            # await message.author.edit(nick=new_nickname)
        except discord.Forbidden:
            print(f"❌ 권한 부족: {message.author} 닉네임 변경 실패")
        except discord.HTTPException as e:
            print(f"⚠️ 닉네임 변경 실패 (HTTPException): {e}")
        except Exception as e:
            print(f"⚠️ 닉네임 변경 실패 (Exception): {e}")

    await bot.process_commands(message)



# 봇 실행 (여기에 본인 토큰 입력)
bot.run("MTQxNDU4MzExMzY5ODI1MDc4Mw.Gh9P2C.JRQIfK4vB00u7PcYS16cDLXPJqjYWUvx1n1PjE")
