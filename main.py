import discord
import os
from discord.ext import commands
from discord import app_commands
import re

from myserver import server_on

# ---------------- CONFIG ----------------
GUILD_ID = 1411573311787241534  # ID เซิร์ฟเวอร์
LOG_CHANNEL_ID = 1412071745137020958  # ช่อง log สำหรับลิ้งทรูมันนี่
TARGET_CHANNEL_ID = 1411575566976417952  # ช่องหลักให้แสดงเมนู

# กำหนด role ID และราคายศ
ROLES_FOR_SALE = {
    1411575321798512751: 15,
    1411586539544252537: 15,
    1411586465896464506: 50,
    1412062520826662974: 100
}

# เก็บ point ของแต่ละ user
user_points = {}

# ---------------- BOT ----------------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# regex ตรวจจับ URL
url_pattern = re.compile(r"https?://[^\s]+")


# ---------------- VIEW ----------------
class MainMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="ดูราคายศ", style=discord.ButtonStyle.primary)
    async def show_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="💎 ราคายศทั้งหมด", color=discord.Color.blue())
        for role_id, price in ROLES_FOR_SALE.items():
            role = interaction.guild.get_role(role_id)
            if role:
                embed.add_field(name=role.name, value=f"{price} Points", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="ซื้อยศ", style=discord.ButtonStyle.success)
    async def buy_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        points = user_points.get(user_id, 0)

        options = []
        for role_id, price in ROLES_FOR_SALE.items():
            role = interaction.guild.get_role(role_id)
            if role:
                options.append(discord.SelectOption(label=f"{role.name} - {price} Points", value=str(role_id)))

        if not options:
            await interaction.response.send_message("❌ ไม่มี Role ที่สามารถซื้อได้", ephemeral=True)
            return

        select = discord.ui.Select(placeholder="เลือกยศที่ต้องการซื้อ", options=options)

        async def select_callback(inter: discord.Interaction):
            role_id = int(select.values[0])
            price = ROLES_FOR_SALE[role_id]

            if user_points.get(user_id, 0) < price:
                await inter.response.send_message("❌ Point ของคุณไม่พอสำหรับการซื้อยศนี้!", ephemeral=True)
                return

            role = inter.guild.get_role(role_id)
            if role:
                await inter.user.add_roles(role)
                user_points[user_id] -= price
                await inter.response.send_message(
                    f"✅ คุณได้ซื้อยศ {role.name} แล้ว! เหลือ {user_points[user_id]} Points",
                    ephemeral=True
                )

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("เลือกยศที่คุณต้องการซื้อ:", view=view, ephemeral=True)

    @discord.ui.button(label="เช็คจำนวน Point", style=discord.ButtonStyle.secondary)
    async def check_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        points = user_points.get(user_id, 0)
        await interaction.response.send_message(f"💰 คุณมี {points} Points", ephemeral=True)

    @discord.ui.button(label="เติมเงิน", style=discord.ButtonStyle.danger)
    async def topup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "💰 กรุณาส่ง **ลิ้งซองทรูมันนี่** ของคุณในแชทนี้ (ข้อความนี้เห็นได้เฉพาะคุณเท่านั้น)",
            ephemeral=True
        )


# ---------------- SLASH COMMAND ----------------
@bot.tree.command(name="addpoin", description="เพิ่ม Point ให้ User")
@app_commands.describe(user="เลือก User ที่จะเพิ่ม Point", amount="จำนวน Point ที่จะเพิ่ม")
async def addpoin(interaction: discord.Interaction, user: discord.Member, amount: int):
    user_points[user.id] = user_points.get(user.id, 0) + amount
    await interaction.response.send_message(
        f"✅ เพิ่ม {amount} Points ให้ {user.mention} ตอนนี้มี {user_points[user.id]} Points",
        ephemeral=True
    )


# ---------------- EVENT ----------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # ตรวจสอบว่าเป็นลิ้งหรือไม่
    if url_pattern.search(message.content):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="📩 มีการส่งลิ้งซองทรูมันนี่",
                description=f"👤 จาก: {message.author.mention}\n🔗 ลิ้ง: {message.content}",
                color=discord.Color.orange()
            )
            await log_channel.send(embed=embed)
        await message.reply("✅ ลิ้งของคุณถูกส่งไปตรวจสอบแล้ว", mention_author=False)

    await bot.process_commands(message)


# ---------------- READY ----------------
@bot.event
async def on_ready():
    streaming = discord.Streaming(
        name="พร้อมใช้งาน💜",
        url="https://www.youtube.com/"
    )
    await bot.change_presence(activity=streaming)
    await bot.tree.sync()
    print(f"✅ บอทออนไลน์แล้ว: {bot.user}")

    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🛒 ขายยศ",
            description="เลือกยศที่ต้องการ 100 points = 1บาท",
            color=discord.Color.green()
        )
        embed.set_image(
            url="https://media.discordapp.net/attachments/1411575487096164522/1411580378254147704/1276_20250831121606.png"
        )
        await channel.send(embed=embed, view=MainMenu())

server_on()

bot.run(os.getenv('TOKEN'))