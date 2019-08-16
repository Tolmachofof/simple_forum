from json import JSONDecodeError

from aiohttp import web
from marshmallow import ValidationError


async def load_data(request, schema):
    try:
        request_data = await request.json()
    except JSONDecodeError:
        raise
    try:
        return schema.load(request_data).data
    except ValidationError as exc:
        raise web.HTTPBadRequest(body=str(exc.messages))
