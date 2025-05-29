import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import traceback
from datetime import *
import random
# Custom Modules
import services.gumiSleep as gs
from services.fansExpSystem import ExpSystem
import const
import serviceList
# Consts

# Configuration
ALLOWED_CHANNEL_IDS = const.ALLOWED_CHANNEL_IDS
ALLOWED_SLASH_COMMAND_CHANNELS = const.ALLOWED_SLASH_COMMAND_CHANNELS
BREAK_LAW_MEMBER = const.BREAK_LAW_MEMBER
GUILD_ID = const.GUILD_ID

# Initialize the Discord client with intents
intents = discord.Intents.default()
intents.message_content = True  # 如果你有 on_message 需求
bot = commands.Bot(command_prefix="!", intents=intents)

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


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild {guild.id}")
        print(bot.tree.get_commands())  # debug print
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.event
async def on_message(message):
    user = getUserData(message)
    print(f"New message: {message.content} from {user["user_nickName"]}({user["user_name"]}) in {message.channel.id}-{message.channel.name}")

    # 確認是否在允許的頻道中
    if ALLOWED_CHANNEL_IDS and message.channel.id not in ALLOWED_CHANNEL_IDS:
        return # Ignore messages from channels not in the allowed list
    # 機器人不要回覆自己的訊息
    if message.author == bot.user:
        return
    # 確認是否有檔案附件
    if message.attachments and bot.user in message.mentions:
        return  # 確保檔案處理後不再執行文字回應邏輯

    # 確認是否標記了機器人（文字訊息處理）
    if bot.user in message.mentions:
        try:
           user = getUserData(message)
           replyMsg = [
               f"嗯呢？{user["user_nickName"]}你叫我嗎？",
               f"嗯呢呢!{user["user_nickName"]}安安!",
               f"哇噠~{user["user_nickName"]}你好，恩呢呢!",
               f"{user["user_nickName"]}~こんにちンナ!"
           ]
           await message.channel.send(random.choice(replyMsg)) 
           return
        except Exception as e:
            # 發送錯誤提示訊息
            await message.channel.send(f"Oops! Something went wrong: {e}")
            return
    
    # 經驗值判定
    if True:
        # print("進入經驗值判定")
        lastUpdate = ExpSystem.getLastUpdate(user)
        res, lastUpdate = ExpSystem.isOverOneMin(lastUpdate)
        # print(f"經驗判定結果{res}:{lastUpdate}")
        if res:
            try:
                expAmt = random.choice([1, 2, 3, 4, 5])
                lvlUp = ExpSystem.updateExpAndLvl(user, expAmt, lastUpdate)
                print(f"✨{user["user_nickName"]}獲得了{expAmt}經驗{lastUpdate}!")
                if lvlUp:
                    lvl = ExpSystem.getLvlData(user)[0]
                    targetChannel = bot.get_channel(const.ANNOUNCEMENT_CHANNEL)
                    cheerMsg = [
                        f"嗯呢呢! {user["user_nickName"]} 恭喜你升到{lvl}級了!",
                        f"哇噠~伊呢嗚吶噠! {user["user_nickName"]} 升到了{lvl}級!",
                        f"哇噠恩呢! {user["user_nickName"]} 升級了! 現在是{lvl}級!"
                    ]
                    await targetChannel.send(random.choice(cheerMsg))
            except Exception as e:
                print(e)
                traceback.print_exc()               

    # 軟糖/狐仙 破戒提醒
    if (user["user_name"] in BREAK_LAW_MEMBER):
        now = datetime.now().time()
        # 狐仙以外的
        if(user["user_name"] != "fairyfoxxx_704"):
            if time(0, 0) <= now <= time(5, 0):
                lastUpdate = gs.get_last_update(user['user_name'])[0]
                # Check last update
                if(datetime.now().date() > datetime.strptime(lastUpdate, '%Y-%m-%d').date()):
                    gs.add_times(user["user_name"])
                    bkTime = gs.get_latest_times(user["user_name"])[0]
                    await message.channel.send(f"{user['user_nickName']}，你今天破戒了嗯呢，累積次數{bkTime}！")
                    return
        # 狐仙
        else:
            if time(12, 0) <= now <= time(17, 0):
                lastUpdate = gs.get_last_update(user['user_name'])[0]
                # Check last update
                if(datetime.now().date() > datetime.strptime(lastUpdate, '%Y-%m-%d').date()):
                    gs.add_times(user["user_name"])
                    bkTime = gs.get_latest_times(user["user_name"])[0]
                    await message.channel.send(f"{user['user_nickName']}，你今天破戒了嗯呢，累積次數{bkTime}！")
                    return
    
    # 特殊指令處理
    if message.content.lower().startswith("!"):
        if message.content == "!serviceList" and user["user_name"] in const.DEVELOPER:
            await message.channel.send(serviceList.SERVICE_LIST)
            return
        if message.content.lower() == "!114514":
            await message.channel.send("1919810")
            return
# Commands
# Run the bot with your Discord token
async def main():
    await bot.load_extension("commands.rankcard")
    await bot.start(const.DISCORD_KEY)
asyncio.run(main())
