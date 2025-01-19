import asyncio
from sys import version as pyver

import pyrogram
from pyrogram import __version__ as pyrover
from pyrogram import filters, idle
from pyrogram.errors import FloodWait, BadMsgNotification
from pyrogram.types import Message

import config
import mongo
from mongo import db

loop = asyncio.get_event_loop()
SUDO_USERS = config.SUDO_USER

app = pyrogram.Client(
    ":YukkiBot:",
    config.API_ID,
    config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

save = {}
grouplist = 1

async def start_bot():
    if app.is_connected:
        print("Bot is already connected.")
        return

    try:
        await app.start()
        print("Bot started successfully!")
    except BadMsgNotification as e:
        if e.error_code == 16:
            print("Time synchronization issue detected. Retrying...")
            await asyncio.sleep(5)
            await start_bot()
        else:
            print(f"Unexpected error occurred: {e}")

async def init():
    await start_bot()

    @app.on_message(filters.command(["start", "help"]))
    async def start_command(_, message: Message):
        if await mongo.is_banned_user(message.from_user.id):
            return
        await mongo.add_served_user(message.from_user.id)

        image_url = "https://telegra.ph/file/4d61a4d43b25f658484b4.jpg"

        welcome_message = (
            "Welcome to Bot! 😊\n\n"
            "Here to assist you with whatever you need.\n\n"
            "**Contact Admin:** [Click Here](t.me/YourAdminLink)\n"
            "**Join Back Up:** [Backup Channel](t.me/YourBackupLink)\n"
            "**Join Main Channel:** [Main Channel](t.me/YourMainChannelLink)\n"
            "\nNote: Forwarding of messages is disabled for privacy. "
            "Please do not share or take screenshots of this conversation."
        )

        await message.reply_photo(
            photo=image_url,
            caption=welcome_message,
            parse_mode="markdown2"
        )

    @app.on_message(filters.command("mode") & filters.user(SUDO_USERS))
    async def mode_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        usage = "**Usage:**\n\n/mode [group | private]\n\n**Group**: All the incoming messages will be forwarded to Log group.\n\n**Private**: All the incoming messages will be forwarded to the Private Messages of SUDO_USERS"
        if len(message.command) != 2:
            return await message.reply_text(usage)
        state = message.text.split(None, 1)[1].strip()
        state = state.lower()
        if state == "group":
            await mongo.group_on()
            await message.reply_text(
                "Group Mode Enabled. All the incoming messages will be forwarded to LOG Group"
            )
        elif state == "private":
            await mongo.group_off()
            await message.reply_text(
                "Private Mode Enabled. All the incoming messages will be forwarded to Private Message of all SUDO_USERs"
            )
        else:
            await message.reply_text(usage)

    @app.on_message(filters.command("block") & filters.user(SUDO_USERS))
    async def block_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        if message.reply_to_message:
            if not message.reply_to_message.forward_sender_name:
                return await message.reply_text(
                    "Please reply to forwarded messages only."
                )
            replied_id = message.reply_to_message_id
            try:
                replied_user_id = save[replied_id]
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Failed to fetch user. You might've restarted bot or some error happened. Please check logs"
                )
            if await mongo.is_banned_user(replied_user_id):
                return await message.reply_text("Already Blocked")
            else:
                await mongo.add_banned_user(replied_user_id)
                await message.reply_text("Banned User from The Bot")
                try:
                    await app.send_message(
                        replied_user_id,
                        "You're now banned from using the Bot by admins.",
                    )
                except:
                    pass
        else:
            return await message.reply_text(
                "Reply to a user's forwarded message to block him from using the bot"
            )

    @app.on_message(filters.command("unblock") & filters.user(SUDO_USERS))
    async def unblock_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        if message.reply_to_message:
            if not message.reply_to_message.forward_sender_name:
                return await message.reply_text(
                    "Please reply to forwarded messages only."
                )
            replied_id = message.reply_to_message_id
            try:
                replied_user_id = save[replied_id]
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Failed to fetch user. You might've restarted bot or some error happened. Please check logs"
                )
            if not await mongo.is_banned_user(replied_user_id):
                return await message.reply_text("Already UnBlocked")
            else:
                await mongo.remove_banned_user(replied_user_id)
                await message.reply_text(
                    "Unblocked User from The Bot"
                )
                try:
                    await app.send_message(
                        replied_user_id,
                        "You're now unbanned from the Bot by admins.",
                    )
                except:
                    pass
        else:
            return await message.reply_text(
                "Reply to a user's forwarded message to unblock him from the bot"
            )

    @app.on_message(filters.command("stats") & filters.user(SUDO_USERS))
    async def stats_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        served_users = len(await mongo.get_served_users())
        blocked = await mongo.get_banned_count()
        text = f""" **ChatBot Stats:**

**Python Version :** {pyver.split()[0]}
**Pyrogram Version :** {pyrover}

**Served Users:** {served_users} 
**Blocked Users:** {blocked}"""
        await message.reply_text(text)

    @app.on_message(filters.command("broadcast") & filters.user(SUDO_USERS))
    async def broadcast_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        if message.reply_to_message:
            x = message.reply_to_message.message_id
            y = message.chat.id
        else:
            if len(message.command) < 2:
                return await message.reply_text(
                    "**Usage**:\n/broadcast [MESSAGE] or [Reply to a Message]"
                )
            query = message.text.split(None, 1)[1]

        susr = 0
        served_users = []
        susers = await mongo.get_served_users()
        for user in susers:
            served_users.append(int(user["user_id"]))
        for i in served_users:
            try:
                await app.forward_messages(
                    i, y, x
                ) if message.reply_to_message else await app.send_message(
                    i, text=query
                )
                susr += 1
            except FloodWait as e:
                flood_time = int(e.x)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except Exception:
                pass
        try:
            await message.reply_text(
                f"**Broadcasted Message to {susr} Users.**"
            )
        except:
            pass

    @app.on_message(filters.private)
    async def incoming_private(_, message):
        # Ignore edited messages
        if message.edit_date:
            return

        user_id = message.from_user.id
        if await mongo.is_banned_user(user_id):
            return
        if user_id in SUDO_USERS:
            if message.reply_to_message:
                if (
                    message.text == "/unblock"
                    or message.text == "/block"
                    or message.text == "/broadcast"
                ):
                    return
                if not message.reply_to_message.forward_sender_name:
                    return await message.reply_text(
                        "Please reply to forwarded messages only."
                    )
                replied_id = message.reply_to_message_id
                try:
                    replied_user_id = save[replied_id]
                except Exception as e:
                    print(e)
                    return await message.reply_text(
                        "Failed to fetch user. You might've restarted bot or some error happened. Please check logs"
                    )
                try:
                    return await app.copy_message(
                        replied_user_id,
                        message.chat.id,
                        message.message_id,
                    )
                except Exception as e:
                    print(e)
                    return await message.reply_text(
                        "Failed to send the message, User might have blocked the bot or something wrong happened. Please check logs"
                    )
        else:
            if await mongo.is_group():
                try:
                    forwarded = await app.forward_messages(
                        config.LOG_GROUP_ID,
                        message.chat.id,
                        message.message_id,
                    )
                    save[forwarded.message_id] = user_id
                except:
                    pass
            else:
                for user in SUDO_USERS:
                    try:
                        forwarded = await app.forward_messages(
                            user, message.chat.id, message.message_id
                        )
                        save[forwarded.message_id] = user_id
                    except:
                        pass

    @app.on_message(filters.group)
    async def incoming_groups(_, message):
        # Ignore edited messages
        if message.edit_date:
            return

        if message.reply_to_message:
            if (
                message.text == "/unblock"
                or message.text == "/block"
                or message.text == "/broadcast"
            ):
                return
            replied_id = message.reply_to_message_id
            if not message.reply_to_message.forward_sender_name:
                return await message.reply_text(
                    "Please reply to forwarded messages only."
                )
            try:
                replied_user_id = save[replied_id]
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Failed to fetch user. You might've restarted bot or some error happened. Please check logs"
                )
            try:
                return await app.copy_message(
                    replied_user_id,
                    message.chat.id,
                    message.message_id,
                )
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Failed to send the message, User might have blocked the bot or something wrong happened. Please check logs"
                )

    print("[LOG] - Yukki Chat Bot Started")
    await idle()

if __name__ == "__main__":
    loop.run_until_complete(init())
