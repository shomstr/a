import asyncio
import os
import tempfile
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from google import genai

# === Настройки ===
API_ID = 29913897
API_HASH = "81d1231df7bb60629ffce9bff0e4c3e5"
BOT_CHAT_ID = 7627986777
GEMINI_API_KEY = "AIzaSyDXe6k8vnuaP_L10VpXVROh2fyVCPSWMiU"  # ← замени на свой

app = Client("my_account", api_id=API_ID, api_hash=API_HASH)

# Инициализируем Gemini
genai_client = genai.Client(api_key="AIzaSyDXe6k8vnuaP_L10VpXVROh2fyVCPSWMiU")
MODEL_NAME = "gemini-1.5-flash"  # или "gemini-3-flash-preview", если доступен

async def solve_captcha_with_gemini(photo_path: str, animal: str) -> str | None:
    """Решает капчу через Gemini: ищет номер квадрата с животным"""
    try:
        with open(photo_path, "rb") as f:
            img_data = f.read()

        # Запрос к модели
        response = genai_client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                genai.types.Part.from_bytes(data=img_data, mime_type="image/jpeg"),
                f"На изображении 9 квадратов с номерами 1-9. Где «{animal}»? Ответь только одной цифрой от 1 до 9."
            ]
        )

        text = response.text.strip()
        print(f"🔍 Gemini ответ: {text}")

        # Извлекаем цифру
        match = re.search(r'\b([1-9])\b', text)
        return match.group(1) if match else None

    except Exception as e:
        print(f"❌ Ошибка в Gemini: {e}")
        return None

@app.on_edited_message(filters.chat(BOT_CHAT_ID))
@app.on_message(filters.chat(BOT_CHAT_ID) & filters.photo)
async def handle_edited_or_photo_message(client: Client, msg: Message):
    text = msg.text or ""
    text_lower = text.lower()

    # 🎯 Обработка капчи: "На какой фотографии изображён «пингвин»?"
    if "на какой фотографии изображён" in text_lower and msg.photo:
        print("🔍 Обнаружена капча!")

        # Извлекаем животное из вопроса
        animal_match = re.search(r'«([^»]+)»', text)
        animal = animal_match.group(1) if animal_match else "животное"
        print(f"🎯 Ищем: {animal}")

        # Скачиваем фото
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        try:
            await client.download_media(msg.photo.file_id, temp_file.name)
            print(f"📥 Фото сохранено: {temp_file.name}")

            # Решаем через Gemini
            answer = await solve_captcha_with_gemini(temp_file.name, animal)
            if answer:
                print(f"✅ Gemini нашёл: {answer}")
                # Отправляем цифру боту
                await client.send_message(BOT_CHAT_ID, answer)
                print(f"📤 Отправлено: '{answer}'")
            else:
                print("❌ Gemini не вернул цифру — пробуем отправить '5' как fallback")
                await client.send_message(BOT_CHAT_ID, "5")

        except Exception as e:
            print(f"❌ Ошибка при обработке капчи: {e}")
        finally:
            os.unlink(temp_file.name)

    # 📋 Обработка заданий (как раньше)
    elif "Запрещено отписываться" in text or "Нажмите на кнопки, чтобы выбрать задание" in text:
        print("⚙️ Обработка задания...")
        for row in msg.reply_markup.inline_keyboard:
            if len(row) != 2:
                continue

            btn1, btn2 = row[0], row[1]

            # URL-кнопка → подписка
            if btn1.url and "t.me/" in btn1.url:
                channel_url = btn1.url
                check_button = btn2

                try:
                    username = channel_url.split("t.me/")[1].split("?")[0]
                    if not any(x in username for x in ["+", "joinchat"]):
                        await client.join_chat(username)
                        print(f"✅ Подписались на @{username}")
                    else:
                        print("⚠️ Приватная ссылка — пропускаем")
                        continue
                except Exception as e:
                    print(f"❌ Ошибка подписки: {e}")
                    continue

                await asyncio.sleep(3)

                # Нажимаем "Проверить"
                if check_button.callback_data:
                    try:
                        await client.request_callback_answer(
                            chat_id=msg.chat.id,
                            message_id=msg.id,
                            callback_data=check_button.callback_data
                        )
                        print("✅ Нажата кнопка 'Проверить'")
                    except Exception as e:
                        print(f"❌ Ошибка при нажатии 'Проверить': {e}")

                await asyncio.sleep(5)

if __name__ == "__main__":
    print("🚀 Запущено: ожидание капчи / заданий от @gram_prbot...")
    app.run()