import discord
from discord import app_commands
import asyncio
from datetime import *
import openai
import os
# Custom Modules
import services.gumiSleep as gs
import const
# Consts

# Configuration
ALLOWED_CHANNEL_IDS = const.ALLOWED_CHANNEL_IDS
ALLOWED_SLASH_COMMAND_CHANNELS = const.ALLOWED_SLASH_COMMAND_CHANNELS
BREAK_LAW_MEMBER = const.BREAK_LAW_MEMBER


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
        await tree.sync()
        print(f"Synced commands to Discord.")
    except Exception as e:
        print(f"Error syncing commands: {e}")
@client.event
async def on_message(message):
    user = getUserData(message)
    print(f"New message: {message.content} from {user["user_nickName"]} in {message.channel.id}-{message.channel.name}")

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
        if message.content.lower() == "!114514":
            await message.channel.send("1919810")
# Slash command to add a task
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
            "抱歉！此指令不能在此頻道使用。", # "Sorry! This command cannot be used in this channel."
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


# Run the bot with your Discord token
client.run(const.DISCORD_KEY)
