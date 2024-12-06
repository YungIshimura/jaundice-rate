from aiohttp import web
import pymorphy2
from main import analyze_urls


async def handle_urls(request: web.Request) -> web.json_response:
    try:
        urls = request.query.get("urls")
        splited_urls = urls.split(",")
        if len(splited_urls) > 10:
            raise web.HTTPBadRequest(text="too many urls in request, should be 10 or less")
        
        morph = request.app["morph"]
        processed_articles = await analyze_urls(splited_urls, morph)
        response = {"analyze results": processed_articles}
    except AttributeError:
        response = {"error": "No links for analysis"}

    return web.json_response(response)


if __name__ == "__main__":
    morph = pymorphy2.MorphAnalyzer()
    app = web.Application()
    app["morph"] = morph
    app.add_routes([web.get("/", handle_urls)])
    web.run_app(app, host="127.0.0.1")
