import logging

from aiohttp import web
from aiojobs.aiohttp import atomic

from ....db.queries import (
    create_post, delete_post, find_posts, get_post, get_post_comments,
    is_post_exist, is_section_exist, update_post
)
from ...utils import load_data
from ..resources import PostSchema, PostsPageSchema

logger = logging.getLogger(__name__)


@atomic
async def create_post_view(request):
    schema = PostSchema()
    post_data = await load_data(request, schema)
    async with request.app['db'].acquire() as conn:
        if not await is_section_exist(conn, post_data['section_id']):
            err_message = (
                'Can not create post. '
                'Section with id {} does not exist'.format(
                    post_data['section_id']
                )
            )
            logger.error(err_message)
            raise web.HTTPBadRequest(body=err_message)
        new_post = await create_post(
            conn, post_data['section_id'], post_data['topic'],
            post_data['description']
        )
        response_data = schema.dump(new_post).data
        return web.json_response(response_data, status=201)


@atomic
async def update_post_view(request):
    schema = PostSchema(strict=True)
    post_id = request.match_info['id']
    post_data = await load_data(request, schema)
    async with request.app['db'].acquire() as conn:
        if not await is_section_exist(conn, post_id):
            logger.error(
                'Cannot update post with id {}. Post does not exist'.format(
                    post_id
                )
            )
            raise web.HTTPNotFound
        updated_post = await update_post(
            conn, post_id, topic=post_data['topic'],
            description=post_data['description']
        )
        post_comments = await get_post_comments(conn, post_id)
        response_data = schema.load({
            'id': updated_post.id,
            'section_id': updated_post.section_id,
            'topic': updated_post.topic,
            'description': updated_post.description,
            'comments': post_comments
        }).data
        return web.json_response(response_data)


async def retrieve_post_view(request):
    schema = PostSchema()
    post_id = request.match_info['id']
    async with request.app['db'].acquire() as conn:
        post = await get_post(conn, post_id)
        if post is None:
            raise web.HTTPNotFound
        post_comments = await get_post_comments(conn, post_id)
        response_data = schema.load({
            'id': post.id,
            'section_id': post.section_id,
            'topic': post.topic,
            'description': post.description,
            'comments': post_comments
        }).data
        return web.json_response(response_data)


async def retrieve_posts_view(request):
    schema = PostsPageSchema()
    query_params = {
        param: request.query_params[param] for param in (
            'topic__like', 'page_num', 'per_page'
        )
    }
    async with request.app['db'].acquire() as conn:
        posts_page = await find_posts(conn, **query_params)
    response_data = schema.dump(posts_page).data
    return web.json_response(response_data)


@atomic
async def delete_post_view(request):
    post_id = request.match_info['id']
    async with request.app['db'].acquire() as conn:
        if not await is_post_exist(conn, post_id):
            logger.error(
                'Cannot delete post with id {}. Post does not exist'.format(
                    post_id
                )
            )
            raise web.HTTPNotFound
        await delete_post(conn, post_id)
        logger.info('Post with id {} was successfully deleted.')
    return web.json_response(status=204)
