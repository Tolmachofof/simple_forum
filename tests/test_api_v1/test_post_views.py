import random

import pytest
from aiohttp import web
from aiojobs.aiohttp import setup as setup_jobs
from sqlalchemy import and_, exists, insert, select

from simple_forum.db.models import comment, post, section
from simple_forum.db.queries import DEFAULT_PAGE_NUM, DEFAULT_PER_PAGE
from simple_forum.routes import POST_URLS


@pytest.fixture
def cli(loop, aiohttp_client, db_engine, cleanup_db):
    app = web.Application()
    app.add_routes(POST_URLS)
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
    
    
@pytest.mark.parametrize(
    'request_data', ({}, {'topic': 'topic'}, {'description': 'description'})
)
async def test_create_post_with_invalid_request_data(request_data, cli):
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'name',
                'description': 'description'
            })
        )
    response = await cli.post(
        '/api/v1/posts', json={'section_id': section_id, **request_data}
    )
    assert response.status == 400
    
    
async def test_update_post(cli):
    request_data = {
        'topic': 'new topic',
        'description': 'new description'
    }
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
        response = await cli.put(
            '/api/v1/posts/{}'.format(post_id),
            json={**{'section_id': section_id}, **request_data}
        )
        assert response.status == 200
        response_data = await response.json()
        assert response_data['topic'] == request_data['topic']
        assert response_data['description'] == request_data['description']
        assert await conn.scalar(
            select([exists().where(
                and_(
                    post.c.id == post_id,
                    post.c.topic == request_data['topic'],
                    post.c.description == request_data['description']
                )
            )])
        )
        
        
async def test_update_post_if_post_does_not_exist(cli):
    post_id = random.randint(1, 100)
    request_data = {
        'section_id': random.randint(1, 100),
        'topic': 'topic',
        'description': 'description'
    }
    response = await cli.put(
        '/api/v1/posts/{}'.format(post_id), json=request_data
    )
    assert response.status == 404
    
    
@pytest.mark.parametrize(
    'request_data', ({}, {'topic': 'topic'}, {'description': 'description'})
)
async def test_update_post_with_invalid_request_data(request_data, cli):
    response = await cli.put(
        '/api/v1/posts/{}'.format(random.randint(1, 100)),
        json=request_data
    )
    assert response.status == 400
    
    
async def retrieve_post(cli):
    post_data = {
        'topic': 'topic',
        'description': 'description'
    }
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'name',
                'description': 'description'
            })
        )
        post_id = await conn.scalar(
            insert(post).values({
                **{'section_id': section_id}, **post_data
            })
        )
        parent_comment_id = await conn.scalar(
            insert(comment).values({'post_id': post_id, 'text': 'text'})
        )
        child_comment_id = await conn.scalar(
            insert(comment).values({
                'post_id': post_id,
                'parent_id': parent_comment_id,
                'text': 'text'
            })
        )
    response = await cli.get('/api/v1/posts/{}'.format(post_id))
    assert response.status == 200
    response_data = await response.json()
    assert response_data['id'] == post_id
    assert response_data['section_id'] == section_id
    assert response_data['topic'] == post_data['topic']
    assert response_data['description'] == post_data['description']
    for _comment in response_data['comments']:
        if _comment['id'] == parent_comment_id:
            assert _comment['children'] == [child_comment_id]
        else:
            assert _comment['parent_id'] == parent_comment_id
            assert not _comment['children']
    
    
async def test_retrieve_post_if_post_does_not_exist(cli):
    response = await cli.get('/api/v1/posts/{}'.format(random.randint(1, 100)))
    assert response.status == 404
    

async def test_retrieve_posts(cli):
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'name',
                'description': 'description'
            })
        )
        target_posts = [
            {
                'id': _id,
                'section_id': section_id,
                'topic': 'topic{}'.format(_id),
                'description': 'description'
            }
            for _id in range(1, 51)
        ]
        other_posts = [
            {
                'id': _id,
                'section_id': section_id,
                'topic': 'other'.format(_id),
                'description': 'description'
            }
            for _id in range(51, 101)
        ]
        await conn.execute(insert(post).values([*target_posts, *other_posts]))
    response = await cli.get(
        '/api/v1/posts', params={'topic__like': 'topic%'}
    )
    assert response.status == 200
    posts_page = await response.json()
    assert posts_page['page_num'] == DEFAULT_PAGE_NUM
    assert posts_page['per_page'] == DEFAULT_PER_PAGE
    assert posts_page['total'] == len(target_posts)
    target_ids = sorted([_post['id'] for _post in target_posts])
    page_ids = sorted([_post['id'] for _post in posts_page['items']])
    assert page_ids == target_ids[:DEFAULT_PER_PAGE]
    
    
async def test_delete_post(cli):
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
        response = await cli.delete('/api/v1/posts/{}'.format(post_id))
        assert response.status == 204
        assert not await conn.scalar(
            select([exists().where(post.c.id == post_id)])
        )


async def test_delete_post_if_post_does_not_exist(cli):
    response = await cli.delete(
        '/api/v1/posts/{}'.format(random.randint(1, 100))
    )
    assert response.status == 404
