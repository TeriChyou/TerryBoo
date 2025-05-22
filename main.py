import discord
from discord import app_commands
import asyncio
from datetime import *
import io
import os
from PIL import Image, ImageDraw, ImageFont # Import Pillow components
import aiohttp # Used for downloading user avatars
import traceback # For error traceback
# Custom Modules
import services.gumiSleep as gs
import const
import serviceList
# Consts

# Configuration
ALLOWED_CHANNEL_IDS = const.ALLOWED_CHANNEL_IDS
ALLOWED_SLASH_COMMAND_CHANNELS = const.ALLOWED_SLASH_COMMAND_CHANNELS
BREAK_LAW_MEMBER = const.BREAK_LAW_MEMBER

try:
    # Attempt to load a common font. You may need to change 'arial.ttf'
    # or provide a full path like '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' on Linux.
    # If the font isn't found, it will fall back to Pillow's default.
    FONT_PATH = r"assets/msjh.ttc" # Or "msyh.ttc" for Windows Simplified Chinese
    # FONT_PATH = "NotoSans-Regular.ttf" # Example for Noto Sans (download from Google Fonts)
    font_large = ImageFont.truetype(FONT_PATH, 40)
    font_medium = ImageFont.truetype(FONT_PATH, 30)
    font_small = ImageFont.truetype(FONT_PATH, 20)
    print(f"Loaded font from: {FONT_PATH}")
except IOError:
    print("Warning: Font file not found or could not be loaded. Using default Pillow font.")
    # Fallback to default font if custom font isn't found
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Initialize the Discord client with intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Set up the command tree for slash commands
tree = app_commands.CommandTree(client)

# Store tasks
tasks = {}

def getUserData(message):
    return {
        "user_id": str(message.author.id),
        "user_name": message.author.name,
        "user_nickName": message.author.display_name,
        "user_discriminator": message.author.discriminator
    }

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    try:
        # Sync the slash commands to Discord
        await tree.sync(guild=const.GUILD_ID)
        print(f"Synced commands to Discord. Guild = {const.GUILD_ID.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")
@client.event
async def on_message(message):
    user = getUserData(message)
    print(f"New message: {message.content} from {user["user_nickName"]}({user["user_name"]}) in {message.channel.id}-{message.channel.name}")

    # 確認是否在允許的頻道中
    if ALLOWED_CHANNEL_IDS and message.channel.id not in ALLOWED_CHANNEL_IDS:
        return # Ignore messages from channels not in the allowed list
    # 機器人不要回覆自己的訊息
    if message.author == client.user:
        return

    # 確認是否有檔案附件
    if message.attachments and client.user in message.mentions:
        return  # 確保檔案處理後不再執行文字回應邏輯

    # 確認是否標記了機器人（文字訊息處理）
    if client.user in message.mentions:
        try:
           user = getUserData(message)
           await message.channel.send(f"嗯呢？{user["user_nickName"]}你叫我嗎？") 
        except Exception as e:
            # 發送錯誤提示訊息
            await message.channel.send(f"Oops! Something went wrong: {e}")
    
    # 軟糖/狐仙 破戒提醒
    if (user["user_name"] in BREAK_LAW_MEMBER):
        now = datetime.now().time()
        # 狐仙以外的
        if(user["user_name"] != "fairyfoxxx_704"):
            if time(0, 0) <= now <= time(7, 0):
                lastUpdate = gs.get_last_update(user['user_name'])[0]
                # Check last update
                if(datetime.now().date() > datetime.strptime(lastUpdate, '%Y-%m-%d').date()):
                    gs.add_times(user["user_name"])
                    bkTime = gs.get_latest_times(user["user_name"])[0]
                    await message.channel.send(f"{user['user_nickName']}，你今天破戒了嗯呢，累積次數{bkTime}！")
        # 狐仙
        else:
            if time(12, 0) <= now <= time(19, 0):
                lastUpdate = gs.get_last_update(user['user_name'])[0]
                # Check last update
                if(datetime.now().date() > datetime.strptime(lastUpdate, '%Y-%m-%d').date()):
                    gs.add_times(user["user_name"])
                    bkTime = gs.get_latest_times(user["user_name"])[0]
                    await message.channel.send(f"{user['user_nickName']}，你今天破戒了嗯呢，累積次數{bkTime}！")

    # 特殊指令處理
    if message.content.lower().startswith("!"):
        if message.content == "!serviceList" and user["user_name"] in const.DEVELOPER:
            await message.channel.send(serviceList.SERVICE_LIST)
        if message.content.lower() == "!114514":
            await message.channel.send("1919810")
# Commands
## Example: add_alarm
@tree.command(name="add_alarm", description="新增事件及參與者")
@app_commands.describe(
    task_name="事件名稱",
    user_mentions="參與者",
    time_value="時間數值(整數)",
)
@app_commands.choices(
    time_unit=[
        app_commands.Choice(name="秒", value="seconds"),
        app_commands.Choice(name="分", value="minutes"),
        app_commands.Choice(name="時", value="hours"),
        app_commands.Choice(name="天", value="days")
    ]
)
async def add_task(
    interaction: discord.Interaction, 
    task_name: str, 
    user_mentions: str, 
    time_value: int, 
    time_unit: app_commands.Choice[str]
):
    if ALLOWED_SLASH_COMMAND_CHANNELS and interaction.channel_id not in ALLOWED_SLASH_COMMAND_CHANNELS:
        await interaction.response.send_message(
            "(>^<;)很抱歉嗯呢！此指令不能在此頻道使用喔 嗯吶~", # "Sorry! This command cannot be used in this channel."
            ephemeral=True # Important: This message is only visible to the user who ran the command.
        )
        return # Stop the command execution here
    # Convert time to seconds
    time_units_in_seconds = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600,
        "days": 86400
    }

    # Get the time unit value
    selected_unit = time_unit.value
    time_in_seconds = time_value * time_units_in_seconds[selected_unit]

    # Parse mentions (split by spaces)
    mentions = user_mentions.split()  # e.g., "@User1 @User2"
    user_ids = [
        int(mention.strip("<@!>")) for mention in mentions
        if mention.startswith("<@") and mention.endswith(">")
    ]

    # Resolve users from IDs
    users = []
    for user_id in user_ids:
        member = interaction.guild.get_member(user_id)
        if not member:
            try:
                # Fetch member from API if not in cache
                member = await interaction.guild.fetch_member(user_id)
            except discord.NotFound:
                continue  # Skip if member is not found
        users.append(member)

    if not users:
        await interaction.response.send_message(
            "No valid users mentioned. Please mention users with @, separated by spaces.",
            ephemeral=True
        )
        return

    # Generate a mention string for all valid users
    user_mentions_resolved = ", ".join(user.mention for user in users)
    print(user_mentions_resolved)
    # Send an acknowledgment message
    await interaction.response.send_message(
        f"{task_name}事件已為{user_mentions_resolved}新增. 將會於{time_value} {selected_unit}後提醒.",
        ephemeral=True
    )

    # Wait for the specified time
    await asyncio.sleep(time_in_seconds)

    # Send the alarm message tagging all users
    await interaction.channel.send(f"⏰{user_mentions_resolved}:該 {task_name}嘍!!")
## Level name card check
# --- New Slash Command: /rank ---
@tree.command(name="my_rank", description="查看你的等級和經驗值(還在開發中)", guild=const.GUILD_ID)
async def rank_command(interaction: discord.Interaction):
    # This is where you'd typically fetch actual data from your database
    # For this example, we'll use placeholder data.
    # In a real bot, you'd get interaction.user.id and query your database.
    if ALLOWED_SLASH_COMMAND_CHANNELS and interaction.channel_id not in ALLOWED_SLASH_COMMAND_CHANNELS:
        await interaction.response.send_message(
            "(>^<;)很抱歉嗯呢！此指令不能在此頻道使用喔 嗯吶~", # "Sorry! This command cannot be used in this channel."
            ephemeral=True # Important: This message is only visible to the user who ran the command.
        )
        return
    user = interaction.user
    user_display_name = user.display_name # Or user.name if you prefer username
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

    # Placeholder Data (replace with your actual data retrieval logic)
    user_rank = 1
    user_level = 114
    user_current_xp = 514
    user_total_xp_for_level = 1919810

    await interaction.response.defer() # Acknowledge the command immediately as image generation can take time

    try:
        rank_card_file = await generate_rank_card(
            user_display_name,
            avatar_url,
            user_rank,
            user_level,
            user_current_xp,
            user_total_xp_for_level
        )
        await interaction.followup.send(file=rank_card_file)
    except Exception as e:
        print(f"Error generating rank card: {e}")
        traceback.print_exc() # <-- 新增這行，它會將完整的錯誤追溯列印到您的程式執行視窗
        await interaction.followup.send("生成等級卡時發生錯誤。")
async def generate_rank_card(
    user_display_name: str,
    avatar_url: str,
    rank: int,
    level: int,
    current_xp: int,
    total_xp_for_level: int
) -> discord.File:
    # Define card dimensions and colors
    card_width, card_height = 800, 200
    background_color = (32, 34, 37, 255) # Dark Discord-like background (RGBA)
    text_color = (255, 255, 255, 255) # White
    xp_bar_background_color = (54, 57, 63, 255) # Darker grey for progress bar background
    xp_bar_fill_color = (255, 127, 255, 255) # Pinkish/Purple for XP fill (like in your image)

    # 1. Create a blank image with a dark background
    img = Image.new('RGBA', (card_width, card_height), background_color)
    draw = ImageDraw.Draw(img)

    # 2. Download and process avatar
    avatar_size = 128
    avatar_x, avatar_y = 30, (card_height - avatar_size) // 2 # Centered vertically
    mask = Image.new('L', (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255) # Circular mask

    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            if resp.status != 200:
                print(f"Failed to download avatar: {resp.status}")
                # Fallback to a placeholder avatar or error handling
                avatar_img = Image.new('RGBA', (avatar_size, avatar_size), (255, 0, 0, 255)) # Red square placeholder
            else:
                avatar_data = io.BytesIO(await resp.read())
                avatar_img = Image.open(avatar_data).convert("RGBA")
                avatar_img = avatar_img.resize((avatar_size, avatar_size))

    # Paste avatar onto the card with the circular mask
    img.paste(avatar_img, (avatar_x, avatar_y), mask)

    # 3. Add Username/Nickname
    username_x = avatar_x + avatar_size + 30
    username_y = card_height // 2 - 50 # Adjust position as needed
    draw.text((username_x, username_y), user_display_name, fill=text_color, font=font_large)

    # 4. Add Rank and Level
    # Rank text
    rank_text = f"RANK #{rank}"
    rank_x_offset = draw.textlength(user_display_name, font=font_large) + 20
    draw.text((username_x + rank_x_offset, username_y + 10), rank_text, fill=(180, 180, 180, 255), font=font_small)

    level_text = f"LV. {level}"
    level_x = card_width - draw.textlength(level_text, font=font_large) - 30
    level_y = username_y
    draw.text((level_x, level_y), level_text, fill=xp_bar_fill_color, font=font_large)


    # 5. Add XP Progress Bar and Text
    xp_bar_width = card_width - username_x - 30
    xp_bar_height = 20
    xp_bar_y = username_y + 70 # Below username

    # Draw XP bar background
    draw.rounded_rectangle(
        (username_x, xp_bar_y, username_x + xp_bar_width, xp_bar_y + xp_bar_height),
        radius=10, fill=xp_bar_background_color
    )

    # Calculate XP fill width
    xp_progress_ratio = current_xp / total_xp_for_level
    xp_fill_width = int(xp_bar_width * xp_progress_ratio)

    # Draw XP bar fill
    draw.rounded_rectangle(
        (username_x, xp_bar_y, username_x + xp_fill_width, xp_bar_y + xp_bar_height),
        radius=10, fill=xp_bar_fill_color
    )

    # Add XP text (e.g., "1.40K / 50.0K XP")
    xp_text = f"{current_xp / 1000:.2f}K / {total_xp_for_level / 1000:.1f}K XP"
    xp_text_x = username_x + xp_bar_width - draw.textlength(xp_text, font=font_small) - 5
    xp_text_y = xp_bar_y - 25
    draw.text((xp_text_x, xp_text_y), xp_text, fill=text_color, font=font_small)


    # 6. Convert image to bytes and return as discord.File
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0) # Rewind the buffer to the beginning
    return discord.File(buffer, filename="rank_card.png")
# Run the bot with your Discord token
client.run(const.DISCORD_KEY)
