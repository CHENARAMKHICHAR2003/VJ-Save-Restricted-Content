import os
import threading
import time
from os import environ
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot Configuration
bot_token = environ.get("TOKEN", "") 
api_hash = environ.get("HASH", "4956e23833905463efb588eb806f9804") 
api_id = int(environ.get("ID", "24894984"))

bot = Client("mybot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
ss = environ.get("STRING", "")
acc = Client("myacc", api_id=api_id, api_hash=api_hash, session_string=ss) if ss else None
if acc:
    acc.start()


# Progress Writer
def progress(current, total, message, type_):
    with open(f'{message.id}{type_}status.txt', "w") as file:
        file.write(f"{current * 100 / total:.1f}%")


# Download Status Function
def download_status(statusfile, message):
    while not os.path.exists(statusfile):
        time.sleep(3)

    while os.path.exists(statusfile):
        with open(statusfile, "r") as file:
            txt = file.read()
        try:
            bot.edit_message_text(message.chat.id, message.id, f"__Downloaded__: **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)


# Upload Status Function
def upload_status(statusfile, message):
    while not os.path.exists(statusfile):
        time.sleep(3)

    while os.path.exists(statusfile):
        with open(statusfile, "r") as file:
            txt = file.read()
        try:
            bot.edit_message_text(message.chat.id, message.id, f"__Uploaded__: **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)


# Handle Private Messages
def handle_private(message, chatid, msgid):
    msg = acc.get_messages(chatid, msgid)
    msg_type = get_message_type(msg)

    if msg_type == "Text":
        bot.send_message(
            message.chat.id, msg.text, entities=msg.entities, reply_to_message_id=message.id
        )
        return

    smsg = bot.send_message(
        message.chat.id, "__Downloading__", reply_to_message_id=message.id
    )
    dosta = threading.Thread(
        target=lambda: download_status(f'{message.id}downstatus.txt', smsg), daemon=True
    )
    dosta.start()

    file = acc.download_media(msg, progress=progress, progress_args=[message, "down"])
    os.remove(f'{message.id}downstatus.txt')

    upsta = threading.Thread(
        target=lambda: upload_status(f'{message.id}upstatus.txt', smsg), daemon=True
    )
    upsta.start()

    thumb = None
    if msg_type == "Document":
        try:
            thumb = acc.download_media(msg.document.thumbs[0].file_id)
        except:
            thumb = None

        bot.send_document(
            message.chat.id,
            file,
            thumb=thumb,
            caption=msg.caption,
            caption_entities=msg.caption_entities,
            reply_to_message_id=message.id,
            progress=progress,
            progress_args=[message, "up"],
        )

    elif msg_type == "Video":
        try:
            thumb = acc.download_media(msg.video.thumbs[0].file_id)
        except:
            thumb = None

        bot.send_video(
            message.chat.id,
            file,
            duration=msg.video.duration,
            width=msg.video.width,
            height=msg.video.height,
            thumb=thumb,
            caption=msg.caption,
            caption_entities=msg.caption_entities,
            reply_to_message_id=message.id,
            progress=progress,
            progress_args=[message, "up"],
        )

    elif msg_type == "Animation":
        bot.send_animation(message.chat.id, file, reply_to_message_id=message.id)

    elif msg_type == "Sticker":
        bot.send_sticker(message.chat.id, file, reply_to_message_id=message.id)

    elif msg_type == "Voice":
        bot.send_voice(
            message.chat.id,
            file,
            caption=msg.caption,
            caption_entities=msg.caption_entities,
            reply_to_message_id=message.id,
            progress=progress,
            progress_args=[message, "up"],
        )

    elif msg_type == "Audio":
        try:
            thumb = acc.download_media(msg.audio.thumbs[0].file_id)
        except:
            thumb = None

        bot.send_audio(
            message.chat.id,
            file,
            caption=msg.caption,
            caption_entities=msg.caption_entities,
            reply_to_message_id=message.id,
            progress=progress,
            progress_args=[message, "up"],
        )

    elif msg_type == "Photo":
        bot.send_photo(
            message.chat.id,
            file,
            caption=msg.caption,
            caption_entities=msg.caption_entities,
            reply_to_message_id=message.id,
        )

    # Cleanup
    if thumb:
        os.remove(thumb)
    os.remove(file)
    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
    bot.delete_messages(message.chat.id, [smsg.id])


# Get Message Type
def get_message_type(msg):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass

    try:
        msg.video.file_id
        return "Video"
    except:
        pass

    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass

    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass

    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass

    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass

    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass

    try:
        msg.text
        return "Text"
    except:
        pass

    return "Unknown"


# Start Command
@bot.on_message(filters.command(["start"]))
def send_start(client, message):
    bot.send_message(
        message.chat.id,
        f"**__👋 Hi {message.from_user.mention}!__**\n"
        "**I am Save Restricted Bot. I can help you save restricted content by its post link.**\n\n{USAGE}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🌐 Update Channel", url="https://t.me/TARGETALLCOURSE")]]
        ),
        reply_to_message_id=message.id
    )


# Save Command
@bot.on_message(filters.text)
def save(client, message):
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
