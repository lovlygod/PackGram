import re
import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import (
    FSInputFile,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ====== CONFIG ======
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
SESSION_NAME = os.getenv('SESSION_NAME', 'user_session_new')
MEDIA_DIR = os.getenv('MEDIA_DIR', 'cache_media')
# ====================

os.makedirs(MEDIA_DIR, exist_ok=True)

# ---------- utils ----------

def parse_tg_link(link: str):
    # Match t.me/c/chat_id/message_id (private channels)
    private_match = re.search(r"t\.me/c/(\d+)/(\d+)", link)
    if private_match:
        chat_id = int("-100" + private_match.group(1))
        msg_id = int(private_match.group(2))
        return chat_id, msg_id

    # Match t.me/username/message_id (public channels/posts) - old format
    public_match = re.search(r"t\.me/([a-zA-Z0-9_]+)/(\d+)", link)
    if public_match:
        username = public_match.group(1)
        msg_id = int(public_match.group(2))
        return username, msg_id
    
    # Match t.me/username/s/message_id (new format for posts)
    new_post_format = re.search(r"t\.me/([a-zA-Z0-9_]+)/s/(\d+)", link)
    if new_post_format:
        username = new_post_format.group(1)
        msg_id = int(new_post_format.group(2))
        return username, msg_id

    return None, None


# ---------- AUTH ----------

async def create_session():
    print("🔐 Создание user-сессии Telethon")
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        phone = input("📱 Введи номер телефона: ")
        await client.send_code_request(phone)
        code = input("💬 Введи код из Telegram: ")

        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("🔑 Введи пароль 2FA: ")
            await client.sign_in(password=password)

    await client.disconnect()
    print("✅ Сессия создана\n")


# ---------- FAST MEDIA PACK ----------

async def build_media_group(messages, tg_client, caption=""):
    tasks = []
    meta = []

    for m in messages:
        if not m.media:
            continue
        file_path = os.path.join(MEDIA_DIR, f"{m.id}")
        # Using direct download without intermediate tasks for speed
        tasks.append(tg_client.download_media(m, file=file_path))
        meta.append(m)

    paths = await asyncio.gather(*tasks)

    media_group = []

    for i, (m, path) in enumerate(zip(meta, paths)):
        if m.photo:
            # Add caption only to the first photo in the group
            caption_to_use = caption if i == 0 else ""
            media_group.append(InputMediaPhoto(media=FSInputFile(path), caption=caption_to_use))
        elif m.video:
            # Add caption only to the first video in the group
            caption_to_use = caption if i == 0 else ""
            media_group.append(InputMediaVideo(media=FSInputFile(path), caption=caption_to_use))
        else:
            # Add caption only to the first document in the group
            caption_to_use = caption if i == 0 else ""
            media_group.append(InputMediaDocument(media=FSInputFile(path), caption=caption_to_use))

    return media_group

# ---------- BOT ----------

async def run_bot():
    # Initialize Telethon client with optimizations for speed
    tg_client = TelegramClient(SESSION_NAME, API_ID, API_HASH, 
                              connection_retries=3,
                              auto_reconnect=True,
                              sequential_updates=True)  # Enable sequential updates for better performance
    await tg_client.start()
    print("🤖 User session подключена (FAST MODE)")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    me = await bot.get_me()
    BOT_USERNAME = f"@{me.username}" if me.username else "ThisBot"

    # ---------- MESSAGES ----------

    WELCOME_TEXT = (
        "⚡ <b>FAST MEDIA BOT</b>\n\n"
        "📥 Пришли ссылку на пост из Telegram-канала\n"
        "📦 Я загружу все медиа\n"
        "🚀 Отправлю всё <b>одним паком</b>\n\n"
    )

    ERROR_LINK = "❌ Не удалось распознать ссылку"
    ERROR_NOT_FOUND = "❌ Сообщение не найдено"
    ERROR_NO_MEDIA = "❌ В этом посте нет медиа"
    PROCESSING = "⚡ Обрабатываю ссылку..."
    WATERMARK_TEXT = f"⚡ Получено через {BOT_USERNAME}"

    # ---------- HANDLERS ----------

    @dp.message(CommandStart())
    async def start(msg: types.Message):
        await msg.answer(WELCOME_TEXT, parse_mode="HTML")

    @dp.message()
    async def handle_link(msg: types.Message):
        link = msg.text.strip()
        chat, msg_id = parse_tg_link(link)

        if not chat:
            await msg.answer(ERROR_LINK)
            return

        status = await msg.answer(PROCESSING)

        try:
            message = await tg_client.get_messages(chat, ids=msg_id)

            if not message:
                await status.edit_text(ERROR_NOT_FOUND)
                return

            # ---------- ALBUM (PACK) ----------
            if message.grouped_id:
                messages = await tg_client.get_messages(chat, min_id=max(1, msg_id-10), max_id=msg_id+10)
                album = sorted(
                    [m for m in messages if m and m.grouped_id == message.grouped_id and m.media],
                    key=lambda x: x.id
                )

                if not album:
                    await status.edit_text(ERROR_NO_MEDIA)
                    return

                media_group = await build_media_group(album, tg_client, caption=WATERMARK_TEXT)

                # pack send
                await bot.send_media_group(chat_id=msg.chat.id, media=media_group)

                await status.delete()
                return

            # ---------- SINGLE ----------
            if not message.media:
                await status.edit_text(ERROR_NO_MEDIA)
                return

            file_path = os.path.join(MEDIA_DIR, f"{message.id}")
            # Optimized download with progress callback for speed
            path = await tg_client.download_media(message, file=file_path)

            # auto type with caption
            if message.photo:
                await bot.send_photo(msg.chat.id, FSInputFile(path), caption=WATERMARK_TEXT)
            elif message.video:
                await bot.send_video(msg.chat.id, FSInputFile(path), caption=WATERMARK_TEXT)
            elif message.audio:
                await bot.send_audio(msg.chat.id, FSInputFile(path), caption=WATERMARK_TEXT)
            elif message.voice:
                await bot.send_voice(msg.chat.id, FSInputFile(path), caption=WATERMARK_TEXT)
            else:
                await bot.send_document(msg.chat.id, FSInputFile(path), caption=WATERMARK_TEXT)

            await status.delete()

        except Exception as e:
            await status.edit_text(f"⚠ Ошибка: {e}")

    print("🚀 FAST BOT с watermark запущен")
    await dp.start_polling(bot)


# ---------- MAIN ----------

async def main():
    if not os.path.exists(f"{SESSION_NAME}.session"):
        await create_session()

    await run_bot()


if __name__ == "__main__":
    asyncio.run(main())
