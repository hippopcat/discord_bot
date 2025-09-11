import discord
from discord.ext import commands, tasks
import re
import asyncio
import os
import random
from datetime import datetime

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------
# 접두사 추출 함수
# -------------------
def extract_prefix(nickname: str) -> str:
    prefix = ""
    bracket_patterns = [
        r'\[[^\]]+\]',
        r'꒰[^꒱]+꒱',
        r'【[^】]+】',
        r'「[^」]+」',
        r'《[^》]+》',
    ]
    combined_pattern = re.compile(r'^(' + '|'.join(bracket_patterns) + r')\s*')
    while match := combined_pattern.match(nickname):
        prefix += match.group(0)
        nickname = nickname[match.end():]

    if prefix and not prefix.endswith(' '):
        prefix += ' '

    special_pattern = re.compile(r'^[#*!~]+')
    if match := special_pattern.match(nickname):
        cleaned = "".join(dict.fromkeys(match.group(0)))  # 중복 제거
        if cleaned:
            prefix += cleaned + ' '

    return prefix

# -------------------
# 전역 상태
# -------------------
nickname_change_enabled = True
all_features_enabled = True
nickname_channel_id = 1414591898366251038  # 닉네임 변경 전용 채널 ID
auto_message_channel_id = 1414591898366251038  # 멘트 보낼 채널 ID (같은 채널로 설정 예시)

# -------------------
# 이벤트
# -------------------
@bot.event
async def on_ready():
    print(f"✅ 로그인 성공: {bot.user}")
    auto_task.start()  # 봇 켜질 때 자동 태스크 시작

@bot.event
async def on_message(message):
    global nickname_change_enabled, all_features_enabled

    if message.author == bot.user:
        return

    content = message.content.strip().lower()

    # ✅ 전용 채널이 아니면 무시
    if message.channel.id != nickname_channel_id:
        return

    # 모든 기능 종료 상태면 무시
    if not all_features_enabled:
        return

    # "off" 입력 시 전체 기능 종료 (채널 내에서만 가능)
    if content == "off":
        all_features_enabled = False
        nickname_change_enabled = False
        await message.channel.send("⚠️ 모든 기능이 종료되었습니다.")
        return

    # ✅ 명령어도 전용 채널에서만 작동
    await bot.process_commands(message)

    # 닉네임 변경 기능 OFF 상태면 무시
    if not nickname_change_enabled:
        return

    # -------------------
    # 닉네임 변경 로직
    # -------------------
    new_name = message.content.strip()
    current_nick = message.author.display_name
    prefix = extract_prefix(current_nick)

    # "삭제" 입력 시 접두사만 유지
    new_nickname = prefix.strip() if new_name == "삭제" else f"{prefix}{new_name}"

    if new_nickname != current_nick:
        try:
            await message.author.edit(nick=new_nickname)
        except discord.Forbidden:
            print(f"권한 부족: {message.author} 닉네임 변경 실패")
        except discord.HTTPException as e:
            print(f"닉네임 변경 실패 (HTTPException): {e}")
        except Exception as e:
            print(f"닉네임 변경 실패 (Exception): {e}")

# -------------------
# 명령어
# -------------------
@bot.command()
async def toggle_nick(ctx):
    """닉네임 변경 기능 ON/OFF 토글"""
    global nickname_change_enabled
    if not all_features_enabled:
        await ctx.send("⚠️ 봇의 모든 기능이 종료되어 사용할 수 없습니다.")
        return
    nickname_change_enabled = not nickname_change_enabled
    status = "✅ 활성화됨" if nickname_change_enabled else "❌ 비활성화됨"
    await ctx.send(f"닉네임 변경 기능이 이제 {status}")

@bot.command()
async def ping(ctx):
    if not all_features_enabled:
        return
    await ctx.send("pong!")

# -------------------
# 자동 실행 기능 (특정 시간에 메시지 + 랜덤 채널 생성)
# -------------------
@tasks.loop(minutes=1)
async def auto_task():
    now = datetime.now().strftime("%H:%M")
    # 예: 매일 12:00에 실행
    if now == "12:00":
        channel = bot.get_channel(auto_message_channel_id)
        if channel:
            await channel.send("⏰ 정해진 시간 알림! 모두 안녕하세요 👋")

            # 랜덤 위치에 채널 생성
            guild = channel.guild
            categories = guild.categories
            if categories:
                random_category = random.choice(categories)
                await guild.create_text_channel(
                    name=f"랜덤-채널-{random.randint(1000,9999)}",
                    category=random_category
                )

# -------------------
# 실행
# -------------------
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("❌ DISCORD_TOKEN 환경변수가 설정되지 않았습니다.")
bot.run(token)