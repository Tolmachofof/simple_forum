import random

import pytest
from aiohttp import web
from aiojobs.aiohttp import setup as setup_jobs
from sqlalchemy import and_, exists, insert, select

from simple_forum.api.v1.views.sections import (
    create_section_view, delete_section_view, retrieve_section_view,
    update_section_view, retrieve_sections_view
)
from simple_forum.db.queries import DEFAULT_PER_PAGE, DEFAULT_PAGE_NUM
from simple_forum.db.models import section


@pytest.fixture
def cli(loop, aiohttp_client, db_engine, cleanup_db):
    app = web.Application()
    app.add_routes((
        web.post(r'/api/v1/sections', create_section_view),
        web.get(r'/api/v1/sections', retrieve_sections_view),
        web.put(r'/api/v1/sections/{id:\d+}', update_section_view),
        web.get(r'/api/v1/sections/{id:\d+}', retrieve_section_view),
        web.delete(r'/api/v1/sections/{id:\d+}', delete_section_view),
    ))
    app['db'] = db_engine
    setup_jobs(app)
    return loop.run_until_complete(aiohttp_client(app))


async def test_create_section(cli):
    request_body = {
        'name': 'section name',
        'description': 'section description'
    }
    response = await cli.post('/api/v1/sections', json=request_body)
    assert response.status == 201
    new_section = await response.json()
    assert new_section['name'] == request_body['name']
    assert new_section['description'] == request_body['description']
    async with cli.server.app['db'].acquire() as conn:
        assert await conn.scalar(select([
            exists().where(
                and_(
                    section.c.id == new_section['id'],
                    section.c.name == new_section['name'],
                    section.c.description == new_section['description']
                )
            )
        ]))

    
@pytest.mark.parametrize(
    'request_body', ({}, {'name': 'name'}, {'description': 'description'})
)
async def test_create_section_with_invalid_request(request_body, cli):
    response = await cli.post('/api/v1/sections', json=request_body)
    assert response.status == 400


async def test_update_section(cli):
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'name', 'description': 'description'
            })
        )
    request_data = {'name': 'new name', 'description': 'new description'}
    response = await cli.put(
        '/api/v1/sections/{}'.format(section_id), json=request_data
    )
    assert response.status == 200
    _section = await response.json()
    assert _section['name'] == request_data['name']
    assert _section['description'] == request_data['description']
    
    
async def test_update_if_section_does_not_exist(cli):
    request_data = {'name': 'new name', 'description': 'new description'}
    response = await cli.put(
        '/api/v1/sections/{}'.format(random.randint(1, 100)), json=request_data
    )
    assert response.status == 404


@pytest.mark.parametrize(
    'request_data',
    ({}, {'name': 'new_name'}, {'description': 'new description'})
)
async def test_update_section_if_request_data_is_invalid(request_data, cli):
    response = await cli.put(
        '/api/v1/sections/{}'.format(random.randint(1, 100)), json=request_data
    )
    assert response.status == 400


async def test_retrieve_section(cli):
    section_data = {'name': 'name', 'description': 'description'}
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(insert(section).values(section_data))
    response = await cli.get('/api/v1/sections/{}'.format(section_id))
    assert response.status == 200
    _section = await response.json()
    assert _section['id'] == section_id
    assert _section['name'] == section_data['name']
    assert _section['description'] == section_data['description']
    
    
async def test_retrieve_section_if_section_does_not_exist(cli):
    response = await cli.get(
        '/api/v1/sections/{}'.format(random.randint(1, 100))
    )
    assert response.status == 404
    
    
async def retrieve_sections(cli):
    target_sections = [
        {
            'id': _id,
            'name': 'target{}'.format(_id),
            'description': 'description'
        }
        for _id in range(1, 51)
    ]
    other_sections = [
        {
            'id': _id,
            'name': 'other{}'.format(_id),
            'description': 'description'
        }
        for _id in range(51, 101)
    ]
    async with cli.server.app['db'].acquire() as conn:
        await conn.execute(
            insert(section).values([*target_sections, *other_sections])
        )
    response = await cli.get(
        '/api/v1/sections', params={'name__like': 'target%'}
    )
    assert response.status == 200
    sections_page = await response.json()
    assert sections_page['page_num'] == DEFAULT_PAGE_NUM
    assert sections_page['per_page'] == DEFAULT_PER_PAGE
    assert sections_page['total'] == len(target_sections)
    target_ids = sorted([_section['id'] for _section in target_sections])
    page_ids = sorted([_section['id'] for _section in sections_page['items']])
    assert page_ids == target_ids


async def test_delete_section(cli):
    async with cli.server.app['db'].acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'name',
                'description': 'description'
            })
        )
    response = await cli.delete('/api/v1/sections/{}'.format(section_id))
    assert response.status == 204
    assert not await conn.scalar(
        select([exists().where(section.c.id == section_id)])
    )


async def test_delete_section_if_section_does_not_exist(cli):
    response = await cli.delete(
        '/api/v1/sections/{}'.format(random.randint(1, 100))
    )
    assert response.status == 404
