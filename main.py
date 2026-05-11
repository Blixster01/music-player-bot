"""
main.py — бот + веб-сервер + PostgreSQL (asyncpg).
DATABASE_URL автоматически берётся из Railway PostgreSQL сервиса.
"""
import asyncio, os, json, hmac, hashlib, urllib.parse
import asyncpg
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN    = os.getenv("BOT_TOKEN",    "YOUR_BOT_TOKEN_HERE")
WEB_APP_URL  = os.getenv("WEB_APP_URL",  "https://your-domain.com/player")
DATABASE_URL = os.getenv("DATABASE_URL", "")   # Railway ставит автоматически

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()
db_pool: asyncpg.Pool = None   # глобальный пул соединений


# ══ DATABASE ══════════════════════════════

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    async with db_pool.acquire() as con:
        await con.execute("""
            CREATE TABLE IF NOT EXISTS favourites (
                user_id  TEXT NOT NULL,
                video_id TEXT NOT NULL,
                title    TEXT,
                channel  TEXT,
                thumb    TEXT,
                added_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT,
                PRIMARY KEY (user_id, video_id)
            )
        """)
    print("✅ PostgreSQL ready")

async def db_get_favs(user_id: str):
    async with db_pool.acquire() as con:
        rows = await con.fetch(
            "SELECT video_id,title,channel,thumb FROM favourites WHERE user_id=$1 ORDER BY added_at DESC",
            user_id
        )
    return [{"id": r["video_id"], "title": r["title"], "channel": r["channel"], "thumb": r["thumb"]} for r in rows]

async def db_add_fav(user_id: str, track: dict):
    async with db_pool.acquire() as con:
        await con.execute(
            """INSERT INTO favourites(user_id,video_id,title,channel,thumb)
               VALUES($1,$2,$3,$4,$5)
               ON CONFLICT(user_id,video_id) DO UPDATE
               SET title=$3, channel=$4, thumb=$5""",
            user_id, track["id"], track.get("title",""), track.get("channel",""), track.get("thumb","")
        )

async def db_remove_fav(user_id: str, video_id: str):
    async with db_pool.acquire() as con:
        await con.execute(
            "DELETE FROM favourites WHERE user_id=$1 AND video_id=$2",
            user_id, video_id
        )


# ══ TELEGRAM INIT DATA VALIDATION ═════════

def validate_init_data(init_data: str):
    """Проверяет подпись Telegram. Возвращает user dict или None."""
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", "")
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received_hash):
            return None
        user = json.loads(parsed.get("user", "{}"))
        return user if user.get("id") else None
    except Exception:
        return None

def get_user_id(request: web.Request):
    init_data = request.headers.get("X-Init-Data", "")
    if not init_data:
        return None
    user = validate_init_data(init_data)
    return str(user["id"]) if user else None

def json_resp(data, status=200):
    return web.Response(
        text=json.dumps(data, ensure_ascii=False),
        content_type="application/json", status=status
    )


# ══ API ROUTES ═════════════════════════════

async def api_get_favs(request: web.Request):
    uid = get_user_id(request)
    if not uid: return json_resp({"error": "unauthorized"}, 401)
    return json_resp(await db_get_favs(uid))

async def api_add_fav(request: web.Request):
    uid = get_user_id(request)
    if not uid: return json_resp({"error": "unauthorized"}, 401)
    try:
        track = await request.json()
        if not track.get("id"): return json_resp({"error": "missing id"}, 400)
        await db_add_fav(uid, track)
        return json_resp({"ok": True})
    except Exception as e:
        return json_resp({"error": str(e)}, 400)

async def api_remove_fav(request: web.Request):
    uid = get_user_id(request)
    if not uid: return json_resp({"error": "unauthorized"}, 401)
    video_id = request.match_info.get("video_id")
    await db_remove_fav(uid, video_id)
    return json_resp({"ok": True})

def cors_headers():
    return {
        "Access-Control-Allow-Origin":  "*",
        "Access-Control-Allow-Headers": "Content-Type, X-Init-Data",
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS"
    }

async def api_options(request: web.Request):
    return web.Response(headers=cors_headers())


# ══ STATIC ═════════════════════════════════

async def handle_player(request: web.Request):
    path = os.path.join(os.path.dirname(__file__), "static", "player.html")
    with open(path, "rb") as f:
        return web.Response(body=f.read(), content_type="text/html")

async def handle_root(request):   raise web.HTTPFound("/player")
async def handle_health(request): return web.Response(text="OK")


# ══ BOT HANDLERS ═══════════════════════════

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎮 Открыть DNO PLAYER", web_app=WebAppInfo(url=WEB_APP_URL))
    ]])
    await message.answer(
        "👾 *DNO PLAYER*\n\nМузыкальный плеер на базе YouTube\\.\nНажми кнопку ниже чтобы открыть ▼",
        parse_mode="MarkdownV2", reply_markup=kb
    )

@dp.message(Command("player"))
async def cmd_player(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="▶ PLAY", web_app=WebAppInfo(url=WEB_APP_URL))
    ]])
    await message.answer("🎵 Открой плеер:", reply_markup=kb)


# ══ MAIN ═══════════════════════════════════

async def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL не задан! Добавь PostgreSQL в Railway и установи переменную.")

    await init_db()

    @web.middleware
    async def cors(request, handler):
        if request.method == "OPTIONS":
            return web.Response(headers=cors_headers())
        resp = await handler(request)
        for k, v in cors_headers().items():
            resp.headers[k] = v
        return resp

    app = web.Application(middlewares=[cors])
    app.router.add_get   ("/",                        handle_root)
    app.router.add_get   ("/player",                  handle_player)
    app.router.add_get   ("/health",                  handle_health)
    app.router.add_get   ("/api/favs",                api_get_favs)
    app.router.add_post  ("/api/favs",                api_add_fav)
    app.router.add_delete("/api/favs/{video_id}",     api_remove_fav)
    app.router.add_route ("OPTIONS", "/api/favs",            api_options)
    app.router.add_route ("OPTIONS", "/api/favs/{video_id}", api_options)

    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    print(f"✅ Web server on port {port}")

    print("✅ Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
