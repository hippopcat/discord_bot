import discord
from discord.ext import commands
import os
import random

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------
# 전역 상태
# -------------------
nickname_change_enabled = True
all_features_enabled = True

nickname_channel_id = 1414591898366251038  # 닉네임 변경 전용 채널
event_target_channel_id = 1415671461334614024  # 이벤트 멘트 채널
ticket_category_id = 1415676436022558784  # 티켓 채널이 생성될 카테고리

# -------------------
# 티켓 버튼 클래스
# -------------------
class TicketButton(discord.ui.View):
    def __init__(self, category: discord.CategoryChannel):
        super().__init__(timeout=None)
        self.category = category

    @discord.ui.button(label="티켓 열기", style=discord.ButtonStyle.green)
    async def open_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        # 티켓 채널 이름
        channel_name = f"ticket-{user.name}"

        # 권한 설정: 유저만 접근
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # 카테고리 가져오기
        category = self.category

        # 티켓 채널 생성
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        await interaction.response.send_message(f"✅ 티켓 채널 {ticket_channel.mention} 생성 완료!", ephemeral=True)

# -------------------
# 이벤트
# -------------------
@bot.event
async def on_ready():
    print(f"✅ 로그인 성공: {bot.user}")

@bot.event
async def on_message(message):
    global nickname_change_enabled, all_features_enabled

    if message.author == bot.user:
        return

    content = message.content.strip()

    # -------------------
    # 이벤트 시작
    # -------------------
    if content == "이벤트 시작!":
        target_channel = bot.get_channel(event_target_channel_id)
        if target_channel:
            # 1️⃣ 멘트 전송
            await target_channel.send("🎉 이벤트 시작! 모두 즐겁게 참여하세요!")

            # 2️⃣ 랜덤 위치에 ??? 채널 생성
            guild = target_channel.guild
            categories = guild.categories
            random_category = random.choice(categories) if categories else None
            new_channel = await guild.create_text_channel(
                name="???",
                category=random_category
            )
            pos = random.randint(0, len(guild.text_channels)-1)
            await new_channel.edit(position=pos)

            # 3️⃣ 랜덤 채널에 티켓 버튼 추가
            ticket_category = guild.get_channel(ticket_category_id)
            if ticket_category and isinstance(ticket_category, discord.CategoryChannel):
                view = TicketButton(ticket_category)
                await new_channel.send("🎫 티켓을 열려면 아래 버튼을 클릭하세요!", view=view)

            await target_channel.send(f"✅ 랜덤 채널 {new_channel.mention} 생성 완료!")

        return  # 이벤트 처리 후 더 이상 메시지 처리하지 않음

    # -------------------
    # 닉네임 변경 기능 처리
    # -------------------
    if message.channel.id == nickname_channel_id and nickname_change_enabled:
        new_name = message.content.strip()
        if new_name.lower() != "삭제":
            try:
                await message.author.edit(nick=new_name)
            except discord.Forbidden:
                print(f"권한 부족: {message.author} 닉네임 변경 실패")
            except discord.HTTPException as e:
                print(f"닉네임 변경 실패 (HTTPException): {e}")
            except Exception as e:
                print(f"닉네임 변경 실패 (Exception): {e}")
        else:
            try:
                await message.author.edit(nick="")
            except:
                pass

    # -------------------
    # 명령어 처리
    # -------------------
    await bot.process_commands(message)

# -------------------
# 명령어
# -------------------
@bot.command()
async def toggle_nick(ctx):
    global nickname_change_enabled
    nickname_change_enabled = not nickname_change_enabled
    status = "✅ 활성화됨" if nickname_change_enabled else "❌ 비활성화됨"
    await ctx.send(f"닉네임 변경 기능이 이제 {status}")

@bot.command()
async def ping(ctx):
    await ctx.send("pong!")

# -------------------
# 실행
# -------------------
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("❌ DISCORD_TOKEN 환경변수가 설정되지 않았습니다.")

bot.run(token)