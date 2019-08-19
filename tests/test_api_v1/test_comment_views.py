import random

import pytest
from aiohttp import web
from aiojobs.aiohttp import setup as setup_jobs
from sqlalchemy import and_, exists, insert, select

from simple_forum.db.models import comment, post, section
from simple_forum.routes import COMMENT_URLS


@pytest.fixture
def cli(loop, aiohttp_client, db_engine, cleanup_db):
    app = web.Application()
    app.add_routes(COMMENT_URLS)
    app['db'] = db_engine
    setup_jobs(app)
    return loop.run_until_complete(aiohttp_client(app))


async def test_create_comment(cli):
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'name',
                'description': 'description'
            })
        )
        post_id = await conn.scalar(
            insert(post).values({
                'section_id': section_id,
                'topic': 'topic',
                'description': 'description'
            })
        )
        request_data = {'post_id': post_id, 'text': 'text'}
        response = await cli.post('/api/v1/comments', json=request_data)
        assert response.status == 201
        response_data = await response.json()
        assert response_data['post_id'] == post_id
        assert response_data['text'] == request_data['text']
        assert await conn.scalar(
            select([exists().where(
                and_(
                    comment.c.id == response_data['id'],
                    comment.c.post_id == post_id,
                    comment.c.text == request_data['text']
                )
            )])
        )


async def test_create_child_comment(cli):
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'name',
                'description': 'description'
            })
        )
        post_id = await conn.scalar(
            insert(post).values({
                'section_id': section_id,
                'topic': 'topic',
                'description': 'description'
            })
        )
        parent_id = await conn.scalar(
            insert(comment).values({'post_id': post_id, 'text': 'text'})
        )
        request_data = {
            'post_id': post_id,
            'text': 'text',
            'parent_id': parent_id
        }
        response = await cli.post('/api/v1/comments', json=request_data)
        assert response.status == 201
        response_data = await response.json()
        assert response_data['post_id'] == post_id
        assert response_data['parent_id'] == parent_id
        assert response_data['text'] == request_data['text']
        assert await conn.scalar(
            select([exists().where(
                and_(
                    comment.c.id == response_data['id'],
                    comment.c.parent_id == parent_id,
                    comment.c.post_id == post_id,
                    comment.c.text == request_data['text']
                )
            )])
        )


async def test_create_comment_if_post_does_not_exist(cli):
    request_data = {'post_id': random.randint(1, 100), 'text': 'text'}
    response = await cli.post('/api/v1/comments', json=request_data)
    assert response.status == 400
    

async def test_create_child_comment_if_parent_does_not_exist(cli):
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'name',
                'description': 'description'
            })
        )
        post_id = await conn.scalar(
            insert(post).values({
                'section_id': section_id,
                'topic': 'topic',
                'description': 'description'
            })
        )
    request_data = {
        'post_id': post_id,
        'text': 'text',
        'parent_id': random.randint(1, 100)
    }
    response = await cli.post('/api/v1/comments', json=request_data)
    assert response.status == 400


async def test_update_comment(cli):
    pass


async def test_update_comment_if_comment_does_not_exist(cli):
    request_data = {'post_id': random.randint(1, 100), 'text': 'new_text'}
    response = await cli.put(
        '/api/v1/comments/{}'.format(random.randint(1, 100)),
        json=request_data
    )
    assert response.status == 404


async def test_delete_comment(cli):
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'name',
                'description': 'description'
            })
        )
        post_id = await conn.scalar(
            insert(post).values({
                'section_id': section_id,
                'topic': 'topic',
                'description': 'description'
            })
        )
        comment_id = await conn.scalar(
            insert(comment).values({
                'post_id': post_id,
                'text': 'text'
            })
        )
        response = await cli.delete('/api/v1/comments/{}'.format(comment_id))
        assert response.status == 204
        assert not await conn.scalar(
            select([exists().where(comment.c.id == comment_id)])
        )


async def test_delete_comment_if_comment_does_not_exist(cli):
    response = await cli.delete(
        '/api/v1/comments/{}'.format(random.randint(1, 100))
    )
    assert response.status == 404
