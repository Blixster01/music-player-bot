import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-domain.com")  # URL где хостится player.html

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎮 Открыть PIXEL PLAYER",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )]
    ])
    await message.answer(
        "👾 *PIXEL PLAYER*\n\n"
        "Музыкальный плеер на базе YouTube\n"
        "Нажми кнопку ниже чтобы открыть ▼",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@dp.message(Command("player"))
async def cmd_player(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="▶ PLAY",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )]
    ])
    await message.answer("🎵 Открой плеер:", reply_markup=keyboard)


async def main():
    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
