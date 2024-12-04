from aiohttp import web

from main import analyze


async def handle(request):
    try:
        urls = request.query.get("urls")
        splited_urls = urls.split(",")
        if len(splited_urls) > 10:
            raise web.HTTPBadRequest
        processed_articles = await analyze(splited_urls)
        response = {"analyze results": processed_articles}
    except web.HTTPBadRequest:
        response = {
            "error": "too many urls in request, should be 10 or less",
            "status": 400,
        }
    except AttributeError:
        response = {"error": "no links for analysis"}

    return web.json_response(response)


app = web.Application()
app.add_routes([web.get("/", handle)])

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.2")
