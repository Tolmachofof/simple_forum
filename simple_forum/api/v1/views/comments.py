from aiohttp import web
from aiojobs.aiohttp import atomic

from ....db.queries import (
    create_comment, delete_comment, is_comment_exist, is_post_exist,
    update_comment
)
from ...utils import load_data
from ..resources import CommentSchema


@atomic
async def create_comment_view(request: web.Request) -> web.Response:
    """View для создания комментария к посту."""
    schema = CommentSchema(strict=True)
    comment_data = await load_data(request, schema)
    async with request.app['db'].acquire() as conn:
        # Проверяем, что пост, к которому оставляется коммент существует
        if not await is_post_exist(conn, comment_data['post_id']):
            raise web.HTTPBadRequest(
                body='Post with id {} does not exist'.format(
                    comment_data['post_id']
                )
            )
        # Если передан id родительского комментария - проверяем,
        # что он существует
        if all((
            comment_data['parent_id'] is not None,
            not await is_comment_exist(conn, comment_data['parent_id'])
        )):
            raise web.HTTPBadRequest(
                body='Comment with id {} does not exist'.format(
                    comment_data['parent_id']
                )
            )
        new_comment = await create_comment(
            conn, comment_data['post_id'], comment_data['text'],
            comment_data.get('parent_id')
        )
        response_data = schema.dump(new_comment).data
        return web.json_response(response_data, status=201)


@atomic
async def update_comment_view(request: web.Request) -> web.Response:
    schema = CommentSchema(strict=True)
    comment_id = request.match_info['id']
    comment_data = await load_data(request, schema)
    async with request.app['db'].acquire() as conn:
        if not await is_comment_exist(conn, comment_id):
            raise web.HTTPNotFound
        updated_comment = await update_comment(
            conn, comment_id, comment_data['text']
        )
        response_data = schema.dump(updated_comment).data
        return web.json_response(response_data)


@atomic
async def delete_comment_view(request):
    comment_id = request.match_info['id']
    async with request.app['db'].acquire() as conn:
        if not await is_comment_exist(conn, comment_id):
            raise web.HTTPNotFound
        await delete_comment(conn, comment_id)
    return web.json_response(status=204)
