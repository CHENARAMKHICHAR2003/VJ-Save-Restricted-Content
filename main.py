import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import time
import os
import threading
from os import environ

# Bot Configuration
bot_token = environ.get("TOKEN", "") 
api_hash = environ.get("HASH", "4956e23833905463efb588eb806f9804") 
api_id = int(environ.get("ID", "24894984"))
bot = Client("mybot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# String Session Setup
ss = environ.get("STRING", "")
if ss:
    acc = Client("myacc", api_id=api_id, api_hash=api_hash, session_string=ss)
    acc.start()
else:
    acc = None


# Download Status Function
def downstatus(statusfile, message):
    while not os.path.exists(statusfile):
        time.sleep(3)

    while os.path.exists(statusfile):
        with open(statusfile, "r") as file:
            txt = file.read()
        try:
            bot.edit_message_text(message.chat.id, message.id, f"__Downloaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)


# Upload Status Function
def upstatus(statusfile, message):
    while not os.path.exists(statusfile):
        time.sleep(3)

    while os.path.exists(statusfile):
        with open(statusfile, "r") as file:
            txt = file.read()
        try:
            bot.edit_message_text(message.chat.id, message.id, f"__Uploaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)


# Progress Writer Function
def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as file:
        file.write(f"{current * 100 / total:.1f}%")


# Start Command
@bot.on_message(filters.command(["start"]))
def send_start(client: pyrogram.Client, message: pyrogram.types.Message):
    bot.send_message(
        message.chat.id,
        f"**__👋 Hi {message.from_user.mention}!__**\n"
        "**I am Save Restricted Bot. I can help you save restricted content by its post link.**\n\n{USAGE}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🌐 Update Channel", url="https://t.me/VJ_Botz")]]
        ),
        reply_to_message_id=message.id
    )


# Save Command
@bot.on_message(filters.text)
def save(client: pyrogram.Client, message: pyrogram.types.Message):
    print(message.text)

    # Joining Chats
    if "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:
        if not acc:
            bot.send_message(message.chat.id, "**String Session is not set.**", reply_to_message_id=message.id)
            return

        try:
            acc.join_chat(message.text)
            bot.send_message(message.chat.id, "**Chat Joined Successfully.**", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            bot.send_message(message.chat.id, "**Chat Already Joined.**", reply_to_message_id=message.id)
        except InviteHashExpired:
            bot.send_message(message.chat.id, "**Invalid Invite Link.**", reply_to_message_id=message.id)
        except Exception as e:
            bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)
        return

    # Getting Messages
    if "https://t.me/" in message.text:
        datas = message.text.split("/")
        from_id = int(datas[-1].split("-")[0].strip())
        to_id = int(datas[-1].split("-")[-1].strip()) if "-" in datas[-1] else from_id

        for msg_id in range(from_id, to_id + 1):
            chat_id = int("-100" + datas[4]) if "https://t.me/c/" in message.text else datas[3]

            if not acc:
                bot.send_message(message.chat.id, "**String Session is not set.**", reply_to_message_id=message.id)
                return

            try:
                handle_private(message, chat_id, msg_id)
            except Exception as e:
                bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)

            time.sleep(3)


# Handle Private Messages
def handle_private(message: pyrogram.types.Message, chat_id, msg_id):
    msg = acc.get_messages(chat_id, msg_id)
    msg_type = get_message_type(msg)

    if msg_type == "Text":
        bot.send_message(message.chat.id, msg.text, entities=msg.entities, reply_to_message_id=message.id)
        return

    smsg = bot.send_message(message.chat.id, "__Downloading__", reply_to_message_id=message.id)
    threading.Thread(target=downstatus, args=(f'{message.id}downstatus.txt', smsg), daemon=True).start()
    file = acc.download_media(msg, progress=progress, progress_args=[message, "down"])
    os.remove(f'{message.id}downstatus.txt')

    threading.Thread(target=upstatus, args=(f'{message.id}upstatus.txt', smsg), daemon=True).start()

    if msg_type == "Document":
        bot.send_document(message.chat.id, file, caption=msg.caption, reply_to_message_id=message.id)
    elif msg_type == "Photo":
        bot.send_photo(message.chat.id, file, caption=msg.caption, reply_to_message_id=message.id)

    os.remove(file)
    os.remove(f'{message.id}upstatus.txt')
    bot.delete_messages(message.chat.id, [smsg.id])


# Get Message Type
def get_message_type(msg: pyrogram.types.Message):
    if msg.document:
        return "Document"
    if msg.photo:
        return "Photo"
    if msg.text:
        return "Text"
    return "Unknown"


# Usage Instructions
USAGE = """**FOR PUBLIC CHATS**

Send post/s link directly.

**FOR PRIVATE CHATS**

1. Send the invite link of the chat.
2. Send post/s link.

**MULTIPLE POSTS**

Send links in the format:
`https://t.me/username/1001-1010`
"""

# Run the Bot
bot.run()
