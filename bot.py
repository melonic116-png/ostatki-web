# -*- coding: utf-8 -*-

import asyncio
import json
import os
from io import BytesIO

import pandas as pd
import requests
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    BufferedInputFile,
)

# ================= НАСТРОЙКИ =================

BOT_TOKEN = "8484694104:AAGa2jPVYGfFec03eQ36hv758gvn9Wumj0k"

WEBAPP_URL = "https://melonic116-png.github.io/ostatki-web/form.html"

RENDER_API_URL = "https://ТВОЙ-RENDER.onrender.com"

# =============================================

storage = MemoryStorage()

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher(storage=storage)


# ================= START =================

@dp.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🧑‍🍳 Кухня",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}?group=kitchen"),
            )],
            [InlineKeyboardButton(
                text="🍹 Бар",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}?group=bar"),
            )],
            [InlineKeyboardButton(
                text="🏭 Цех",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}?group=ceh"),
            )],
        ]
    )

    await message.answer(
        "Выбери раздел для инвентаризации 👇\n\n"
        "После сохранения Excel придёт автоматически.",
        reply_markup=kb,
    )


# ================= WEB APP HANDLER =================

@dp.message(lambda m: m.web_app_data is not None)
async def handle_webapp(message: Message):
    try:
        payload = json.loads(message.web_app_data.data)
    except Exception:
        await message.answer("❌ Ошибка данных")
        return

    if payload.get("action") != "export_excel":
        return

    group = payload.get("group")
    user_id = message.from_user.id

    try:
        response = requests.get(
            f"{RENDER_API_URL}/data",
            params={"user_id": user_id, "group": group},
            timeout=20
        )
        response.raise_for_status()
    except Exception as e:
        await message.answer("❌ Ошибка получения данных с сервера")
        return

    data = response.json()

    if not isinstance(data, list) or not data:
        await message.answer("⚠ Нет данных для выгрузки")
        return

    df = pd.DataFrame(data)

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    file_bytes = buffer.getvalue()

    await message.answer_document(
        BufferedInputFile(
            file_bytes,
            filename=f"{group}_ostatki.xlsx"
        ),
        caption="✅ Excel сформирован автоматически"
    )


# ================= MAIN =================

async def main():
    print("🚀 Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())