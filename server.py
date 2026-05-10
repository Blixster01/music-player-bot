"""
Простой HTTPS-сервер для хостинга player.html.
Telegram Web App требует HTTPS — используй ngrok для тестирования
или задеплой на любой хостинг (Render, Railway, VPS и т.д.)
"""
from aiohttp import web
import os

async def handle_player(request):
    with open("static/player.html", "rb") as f:
        return web.Response(body=f.read(), content_type="text/html")

async def handle_root(request):
    raise web.HTTPFound("/player")

app = web.Application()
app.router.add_get("/", handle_root)
app.router.add_get("/player", handle_player)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Server running on port {port}")
    web.run_app(app, port=port)
