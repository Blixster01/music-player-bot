"""
main.py — запускает бота и веб-сервер одновременно в одном процессе.
Используй этот файл для деплоя на Railway / Render / VPS.
"""
import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-domain.com/player")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ── BOT HANDLERS ──

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🎮 Открыть PIXEL PLAYER",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )
    ]])
    await message.answer(
        "👾 *PIXEL PLAYER*\n\n"
        "Музыкальный плеер на базе YouTube\\.\n"
        "Нажми кнопку ниже чтобы открыть ▼",
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )

@dp.message(Command("player"))
async def cmd_player(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="▶ PLAY", web_app=WebAppInfo(url=WEB_APP_URL))
    ]])
    await message.answer("🎵 Открой плеер:", reply_markup=keyboard)


# ── WEB SERVER ──

async def handle_player(request):
    player_path = os.path.join(os.path.dirname(__file__), "static", "player.html")
    with open(player_path, "rb") as f:
        return web.Response(body=f.read(), content_type="text/html")

async def handle_root(request):
    raise web.HTTPFound("/player")

async def handle_health(request):
    return web.Response(text="OK")


# ── MAIN ──

async def main():
    # Web server
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/player", handle_player)
    app.router.add_get("/health", handle_health)

    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ Web server started on port {port}")

    # Bot polling
    print("✅ Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
