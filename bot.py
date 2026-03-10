# -*- coding: utf-8 -*-

import asyncio
import json
import os
import re
from datetime import datetime

import pandas as pd
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    FSInputFile,
)

BOT_TOKEN = "8484694104:AAGa2jPVYGfFec03eQ36hv758gvn9Wumj0k"

WEBAPP_URL = "https://melonic116-png.github.io/ostatki-web/form.html"

WORK_FILE = "ostatki_current.xlsx"
BACKUP_DIR = "backups"

os.makedirs(BACKUP_DIR, exist_ok=True)

storage = MemoryStorage()
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=storage)


class Finish(StatesGroup):
    waiting_name = State()


def ensure_excel():
    if not os.path.exists(WORK_FILE):
        pd.DataFrame(
            columns=["Наименование", "Кол-во"]
        ).to_excel(WORK_FILE, index=False)


def apply_items(items: list[dict]):
    ensure_excel()
    df = pd.read_excel(WORK_FILE)

    for it in items:
        name = str(it.get("name", "")).strip()
        qty = it.get("qty", 0)

        if not name:
            continue

        mask = df["Наименование"].astype(str).str.lower() == name.lower()
        if mask.any():
            df.loc[mask, "Кол-во"] = qty
        else:
            df.loc[len(df)] = [name, qty]

    df.to_excel(WORK_FILE, index=False)


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
        "1️⃣ Заполни форму\n"
        "2️⃣ Нажми «Готово»\n"
        "3️⃣ Вставь JSON сюда\n"
        "4️⃣ Напиши <b>готово</b>",
        reply_markup=kb,
    )


@dp.message(StateFilter(None))
async def collect(message: Message, state: FSMContext):
    text = (message.text or "").strip()

    if text.lower() == "готово":
        await message.answer("📁 Как назвать файл?")
        await state.set_state(Finish.waiting_name)
        return

    try:
        items = json.loads(text)
        if not isinstance(items, list):
            return
    except Exception:
        return

    apply_items(items)
    await message.answer(f"✅ Принято {len(items)} позиций")


@dp.message(StateFilter(Finish.waiting_name))
async def finish(message: Message, state: FSMContext):
    name_raw = message.text or "ostatki"
    safe = re.sub(r'[\\/*?:"<>|]', "_", name_raw)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    ensure_excel()
    path = os.path.join(BACKUP_DIR, f"{safe}_{ts}.xlsx")
    pd.read_excel(WORK_FILE).to_excel(path, index=False)

    await message.answer_document(
        FSInputFile(path),
        caption=f"✅ Файл сохранён: <b>{safe}</b>",
    )

    os.remove(WORK_FILE)
    await state.clear()


async def main():
    ensure_excel()
    print("🚀 Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
