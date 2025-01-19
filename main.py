import asyncio
from sys import version as pyver

import pyrogram
from pyrogram import __version__ as pyrover
from pyrogram import filters, idle
from pyrogram.errors import FloodWait, BadMsgNotification
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

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

@app.on_message(filters.command("start"))
async def start_command(_, m: Message):
    if await mongo.is_banned_user(m.from_user.id):
        return
    await mongo.add_served_user(m.from_user.id)

    image_url = "https://telegra.ph/file/4d61a4d43b25f658484b4.jpg"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔗 Join Main Channel", url="https://t.me/TechMonXz"),
                InlineKeyboardButton("🔗 Join Backup Channel", url="https://t.me/TechMonUPSC_2")
            ],
            [
                InlineKeyboardButton("➕ Add me to your Group ➕", url="https://t.me/SDAutoApproveBot?startgroup")
            ]
        ]
    )

    welcome_message = (
        f"**🦊 Hello {m.from_user.mention}!\n**\n"
        "I'm an auto-approve bot here to assist you. 🌟\n"
        "I can approve users in your groups or channels.\n"
        "Add me to your chat and promote me to admin with 'Add Members' permission for full functionality.\n\n"
        "For more details, check out the channels below:\n"
        "• [Main Channel: TechMonXz](https://t.me/TechMonXz)\n"
        "• [Backup Channel: TechMonUPSC_2](https://t.me/TechMonUPSC_2)\n\n"
        "Feel free to reach out if you need any help! 😊"
    )

    await m.reply_photo(
        photo=image_url,
        caption=welcome_message,
        reply_markup=keyboard,
        parse_mode="html"
    )


@app.on_message(filters.private)
async def incoming_private(_, message: Message):
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

    print(f"[LOG] - {message.from_user.first_name} started the bot!")
    
print("[LOG] - Yukki Chat Bot Started")
await idle()

if __name__ == "__main__":
    app.run()  # This ensures the bot keeps running
