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
            bot.loop.create_task(bot.edit_message_text(message.chat.id, message.id, f"__Downloaded__: **{txt}**"))
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
            bot.loop.create_task(bot.edit_message_text(message.chat.id, message.id, f"__Uploaded__: **{txt}**"))
            time.sleep(10)
        except:
            time.sleep(5)


# Handle Private Messages
async def handle_private(message, chatid, msgid):
    try:
        msg = await acc.get_messages(chatid, msgid)
        msg_type = get_message_type(msg)

        # Ensure msg is not None and has the required attributes before proceeding
        if not msg:
            await bot.send_message(message.chat.id, "**Error**: Message not found.", reply_to_message_id=message.id)
            return
        
        # Handle Text messages separately
        if msg_type == "Text":
            await bot.send_message(
                message.chat.id, msg.text, entities=msg.entities, reply_to_message_id=message.id
            )
            return

        smsg = await bot.send_message(
            message.chat.id, "__Downloading__", reply_to_message_id=message.id
        )
        dosta = threading.Thread(
            target=lambda: download_status(f'{message.id}downstatus.txt', smsg), daemon=True
        )
        dosta.start()

        # Check if the message contains media, handle accordingly
        if not msg.media:
            await bot.send_message(message.chat.id, "**Error**: No media found in this message.", reply_to_message_id=message.id)
            return

        # Download the media
        file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
        if not file:
            await bot.send_message(message.chat.id, "**Error**: Failed to download the file.", reply_to_message_id=message.id)
            return
        os.remove(f'{message.id}downstatus.txt')

        # Upload the file
        upsta = threading.Thread(
            target=lambda: upload_status(f'{message.id}upstatus.txt', smsg), daemon=True
        )
        upsta.start()

        thumb = None
        if msg_type == "Document":
            try:
                thumb = await acc.download_media(msg.document.thumbs[0].file_id) if msg.document.thumbs else None
            except Exception as e:
                print(f"Error downloading document thumbnail: {e}")
                thumb = None

            await bot.send_document(
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
                thumb = await acc.download_media(msg.video.thumbs[0].file_id) if msg.video.thumbs else None
            except Exception as e:
                print(f"Error downloading video thumbnail: {e}")
                thumb = None

            await bot.send_video(
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
            await bot.send_animation(message.chat.id, file, reply_to_message_id=message.id)

        elif msg_type == "Sticker":
            await bot.send_sticker(message.chat.id, file, reply_to_message_id=message.id)

        elif msg_type == "Voice":
            await bot.send_voice(
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
                thumb = await acc.download_media(msg.audio.thumbs[0].file_id) if msg.audio.thumbs else None
            except Exception as e:
                print(f"Error downloading audio thumbnail: {e}")
                thumb = None

            await bot.send_audio(
                message.chat.id,
                file,
                caption=msg.caption,
                caption_entities=msg.caption_entities,
                reply_to_message_id=message.id,
                progress=progress,
                progress_args=[message, "up"],
            )

        elif msg_type == "Photo":
            await bot.send_photo(
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
        await bot.delete_messages(message.chat.id, [smsg.id])

    except Exception as e:
        print(f"Error handling message {msgid}: {e}")
        await bot.send_message(message.chat.id, f"**Error**: {e}", reply_to_message_id=message.id)


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
async def send_start(client, message):
    await bot.send_message(
        message.chat.id,
        f"**👋 Hi {message.from_user.mention}, CHOUDHARY Ji!**\n\n"
"**I am Save Restricted Bot, I can send you restricted content by its post link.**\n\n"
"🔹 **FOR PUBLIC CHATS**\n"
"Just send post(s) link.\n\n"
"🔹 **FOR PRIVATE CHATS**\n"
"First send invite link of the chat (unnecessary if the account of string session is already a member of the chat),\n"
"then send post(s) link.\n\n"
"🔹 **FOR BOT CHATS**\n"
"Send link with '/b/', bot's username and message id. You might want to install some unofficial clients to get the ID like below:\n\n"
"Example: `https://t.me/b/botusername/4321`\n\n"
"🔹 **MULTI POSTS**\n"
"Send public/private post links as explained above with the format `from - to` to send multiple messages, like below:\n\n"
"`https://t.me/xxxx/1001-1010`\n\n"
"`https://t.me/c/xxxx/101-120`\n\n"
"Note: Spaces in between don't matter.\n\n"
"If you have any queries, feel free to ask!"
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🌐 Update Channel", url="https://t.me/TARGETALLCOURSE")]]
        ),
        reply_to_message_id=message.id
    )


# Save Command
@bot.on_message(filters.text)
async def save(client, message):
    print(message.text)

    # Joining Chats
    if "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:
        if not acc:
            await bot.send_message(message.chat.id, "**String Session is not set.**", reply_to_message_id=message.id)
            return

        try:
            await acc.join_chat(message.text)
            await bot.send_message(message.chat.id, "**Chat Joined Successfully.**", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await bot.send_message(message.chat.id, "**Chat Already Joined.**", reply_to_message_id=message.id)
        except InviteHashExpired:
            await bot.send_message(message.chat.id, "**Invalid Invite Link.**", reply_to_message_id=message.id)
        except Exception as e:
            await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)
        return

    # Getting Messages
    if "https://t.me/" in message.text:
        datas = message.text.split("/")
        from_id = int(datas[-1].split("-")[0].strip())
        to_id = int(datas[-1].split("-")[-1].strip()) if "-" in datas[-1] else from_id

        for msg_id in range(from_id, to_id + 1):
            await handle_private(message, from_id, msg_id)

# Run the bot
bot.run()
