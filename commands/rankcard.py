import discord
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont # Import Pillow components
import aiohttp # Used for downloading user avatars
import traceback # For error traceback
import io
# Custom Modules
from services.customRankCard import CustomRkCard
from services.fansExpSystem import ExpSystem
import const

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


# Other functions:
def getUserData(obj):
    # 如果是 Message 物件
    if hasattr(obj, "author"):
        user = obj.author
    # 如果是 Interaction 物件
    elif hasattr(obj, "user"):
        user = obj.user
    # 如果是 User/Member 物件本體
    else:
        user = obj

    return {
        "user_id": str(user.id),
        "user_name": user.name,
        "user_nickName": user.display_name,
        "user_discriminator": user.discriminator
    }

async def generate_rank_card(
    user_display_name: str,
    avatar_url: str,
    rank: int,
    level: int,
    current_xp: int,
    total_xp_for_level: int,
    theme_color
) -> discord.File:
    # Define card dimensions and colors
    card_width, card_height = 800, 200
    background_color = (32, 34, 37, 255) # Dark Discord-like background (RGBA)
    text_color = (255, 255, 255, 255) # White
    xp_bar_background_color = (54, 57, 63, 255) # Darker grey for progress bar background
    xp_bar_fill_color = theme_color 

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
    fontSize = font_large
    if 16 > len(user_display_name) > 8: # user name len judge
        fontSize = font_medium
        username_y = username_y + 5
    else:
        fontSize = font_small
        username_y = username_y + 10
    draw.text((username_x, username_y), user_display_name, fill=text_color, font=fontSize)

    # 4. Add Rank and Level
    # Level Text
    level_text = "Lv. "
    level_val = f"{level}"
    level_x = card_width - draw.textlength(level_text, font=font_small) - draw.textlength(level_val, font=font_medium) - 30
    level_y = username_y - 30
    draw.text((level_x, level_y + 10), level_text, fill=xp_bar_fill_color, font=font_small)
    draw.text((level_x + draw.textlength(level_text, font=font_small), level_y), level_val, fill=xp_bar_fill_color, font=font_medium)
    # Rank Text
    rank_text = f"RANK "
    rank_val = f"#{rank}"
    rank_x = level_x - draw.textlength(rank_text, font=font_small) - draw.textlength(rank_val, font=font_medium) - 10
    rank_y = username_y - 30
    draw.text((rank_x,  rank_y + 10), rank_text, fill=(180, 180, 180, 255), font=font_small)
    draw.text((rank_x + draw.textlength(rank_text, font=font_small),  rank_y), rank_val, fill=(180, 180, 180, 255), font=font_medium)


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

    # Add XP text (e.g., "1.40K / 50.0K XP") if > 1000 then K
    curr_xp = f"{current_xp}"
    total_xp = f"{total_xp_for_level}"

    if 1000000 > current_xp > 1000:
        curr_xp = f"{current_xp / 1000:.2f}K"
    elif current_xp > 1000000:
        curr_xp = f"{current_xp / 1000000:.2f}M"
    if 1000000 > total_xp_for_level > 1000:
        total_xp = f"{total_xp_for_level / 1000:.1f}K"
    elif total_xp_for_level > 1000000:
        total_xp = f"{total_xp_for_level / 1000000:.1f}M"

    xp_text = f"{curr_xp} / {total_xp} XP"
    xp_text_x = username_x + xp_bar_width - draw.textlength(xp_text, font=font_small) - 5
    xp_text_y = xp_bar_y - 25
    draw.text((xp_text_x, xp_text_y), xp_text, fill=text_color, font=font_small)


    # 6. Convert image to bytes and return as discord.File
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0) # Rewind the buffer to the beginning
    return discord.File(buffer, filename="rank_card.png")

# Class
class RankCard(app_commands.Group):
    ## commands
    """
    @app_commands.command(name="test", description="測試指令")
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ennnen?")

    """
    @app_commands.command(name="my_rank", description="查看你的排名、等級和經驗值")
    async def rank_command(self, interaction: discord.Interaction):
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
        user_id = getUserData(user)["user_id"] 
        # Placeholder Data (replace with your actual data retrieval logic)
        res = ExpSystem.getLvlData(getUserData(user))
        user_rank = ExpSystem.getUserRank(user_id)
        user_level = res[0]
        user_current_xp = res[1]
        user_total_xp_for_level = res[2]
        color_set = CustomRkCard.get_or_create_RGB(user_id)
        color = (color_set[0], color_set[1], color_set[2], 255) # Pinkish/Purple for XP fill (like in your image)

        await interaction.response.defer() # Acknowledge the command immediately as image generation can take time

        try:
            rank_card_file = await generate_rank_card(
                user_display_name,
                avatar_url,
                user_rank,
                user_level,
                user_current_xp,
                user_total_xp_for_level,
                color
            )
            await interaction.followup.send(file=rank_card_file)
        except Exception as e:
            print(f"Error generating rank card: {e}")
            traceback.print_exc() # <-- 新增這行，它會將完整的錯誤追溯列印到您的程式執行視窗
            await interaction.followup.send("生成等級卡時發生錯誤。")

    @app_commands.command(name="set_card_color", description="設定你的等級卡顏色(目前只支援等級字體/經驗條)")
    @app_commands.describe(
        red_val="R值",
        green_val="G值",
        blue_val="B值"
    )
    async def set_card_color(
        self,
        interaction: discord.Interaction,
        red_val: int, green_val: int, blue_val: int
    ):
        # Check channel
        if ALLOWED_SLASH_COMMAND_CHANNELS and interaction.channel_id not in ALLOWED_SLASH_COMMAND_CHANNELS:
            await interaction.response.send_message(
                "(>^<;)很抱歉嗯呢！此指令不能在此頻道使用喔 嗯吶~",
                ephemeral=True # Important: This message is only visible to the user who ran the command.
            )
            return
        # Get user
        user = getUserData(interaction.user)
        # check if value are over or under
        if (red_val > 255 or red_val < 0) or (green_val > 255 or green_val < 0) or (blue_val > 255 or blue_val < 0):
            await interaction.response.send_message(
                "(≖_≖...) RGB的上下限是0~255呢 請重新輸入嗯呢!",
                ephemeral=True
                )
            return
        
        try:
            res = CustomRkCard.setRGB(user["user_id"], red_val, green_val, blue_val)
            if res:
                await interaction.response.send_message(
                "(>v<)! 嗯呢! 等級卡的顏色設定成功了呢!",
                ephemeral=True
                )
                return
            else:
                await interaction.response.send_message(
                "(˃̣̣̥ᯅ˂̣̣̥)很抱歉嗯呢！設定失敗了，請洽泰瑞布本布",
                ephemeral=True
                )
                return
        except Exception as e:
            print(e)
            traceback.print_exc() # TraceBack
            return
     
# 4. 只在 setup 註冊一次 group
async def setup(bot):
    bot.tree.add_command(RankCard(name="rank", description="等級卡相關指令"))
    print("RankCard loaded!")  # debug print
        
        
