import random

import pytest
from aiohttp import web
from aiojobs.aiohttp import setup as setup_jobs
from sqlalchemy import exists, insert, select

from simple_forum.api.v1.views.posts import (
    create_post_view
)
from simple_forum.db.models import section, post


@pytest.fixture
def cli(loop, aiohttp_client, db_engine, cleanup_db):
    app = web.Application()
    app.add_routes((
        web.post(r'/api/v1/posts', create_post_view),
    ))
    app['db'] = db_engine
    setup_jobs(app)
    return loop.run_until_complete(aiohttp_client(app))


async def test_create_post(cli):
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'name',
                'description': 'description'
            })
        )
        request_data = {
            'section_id': section_id,
            'topic': 'topic',
            'description': 'description'
        }
        response = await cli.post('/api/v1/posts', json=request_data)
        assert response.status == 201
        new_post = await response.json()
        assert new_post['section_id'] == section_id
        assert new_post['topic'] == request_data['topic']
        assert new_post['description'] == request_data['description']
        assert await conn.scalar(
            select([exists().where(post.c.id == new_post['id'])])
        )
        

async def test_create_post_if_section_does_not_exist(cli):
    request_data = {
        'section_id': random.randint(1, 100),
        'topic': 'topic',
        'description': 'description'
    }
    response = await cli.post('/api/v1/posts', json=request_data)
    assert response.status == 400
