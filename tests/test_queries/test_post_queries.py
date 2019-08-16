import random
from datetime import datetime
from unittest import mock

import pytest
from sqlalchemy import ColumnDefault, and_, exists, insert, select

from simple_forum.db.models import post, section
from simple_forum.db.queries import (
    create_post, delete_post, get_post, is_post_exist, update_post
)


async def test_create_post(db_engine, cleanup_db):
    post_topic = 'post topic'
    post_description = 'post description'
    dt_now = datetime.utcnow()
    async with db_engine.acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'section name',
                'description': 'section description'
            })
        )
        with mock.patch.object(
            post.c.created_at, 'default',
            new=ColumnDefault(lambda: dt_now)
        ):
            new_post = await create_post(
                conn, section_id, post_topic, post_description
            )
            assert new_post.section_id == section_id
            assert new_post.topic == post_topic
            assert new_post.description == post_description
            assert new_post.created_at == dt_now
            assert await conn.scalar(
                select([exists().where(
                    and_(
                        post.c.id == new_post.id,
                        post.c.section_id == section_id,
                        post.c.topic == post_topic,
                        post.c.description == post_description,
                        post.c.created_at == dt_now
                    )
                )])
            )


async def test_is_post_exist(db_engine, cleanup_db):
    async with db_engine.acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'section name',
                'description': 'section description'
            })
        )
        post_id = await conn.scalar(
            insert(post).values({
                'section_id': section_id,
                'topic': 'post topic',
                'description': 'post description'
            })
        )
        assert await is_post_exist(conn, post_id)


async def test_is_post_exist_if_post_does_not_exist(db_engine):
    async with db_engine.acquire() as conn:
        assert not await is_post_exist(conn, random.randint(1, 100))
        

async def test_get_post(db_engine, cleanup_db):
    post_topic = 'post topic'
    post_description = 'post description'
    dt_now = datetime.utcnow()
    async with db_engine.acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'section name',
                'description': 'section description'
            })
        )
        with mock.patch.object(
            post.c.created_at, 'default',
            new=ColumnDefault(lambda: dt_now)
        ):
            post_id = await conn.scalar(
                insert(post).values({
                    'section_id': section_id,
                    'topic': 'post topic',
                    'description': 'post description'
                })
            )
        _post = await get_post(conn, post_id)
        assert _post is not None
        assert _post.section_id == section_id
        assert _post.topic == post_topic
        assert _post.description == post_description
        assert _post.created_at == dt_now


async def test_get_post_if_post_does_not_exist(db_engine):
    async with db_engine.acquire() as conn:
        assert await get_post(conn, random.randint(1, 100)) is None
        

async def test_update_post(db_engine, cleanup_db):
    new_topic = 'new topic'
    new_description = 'new description'
    dt_now = datetime.utcnow()
    async with db_engine.acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'section name',
                'description': 'section description'
            })
        )
        post_id = await conn.scalar(
            insert(post).values({
                'section_id': section_id,
                'topic': 'post topic',
                'description': 'post description'
            })
        )
        with mock.patch.object(
            post.c.updated_at, 'default',
            new=ColumnDefault(lambda: dt_now)
        ):
            updated_post = await update_post(
                conn, post_id, topic=new_topic, description=new_description
            )
            assert updated_post is not None
            assert updated_post.topic == new_topic
            assert updated_post.description == new_description
            assert updated_post.updated_at == dt_now
            assert await conn.scalar(
                select([exists().where(
                    and_(
                        post.c.id == post_id,
                        post.c.topic == new_topic,
                        post.c.description == new_description,
                        post.c.updated_at == dt_now
                    )
                )])
            )


async def test_delete_post(db_engine, cleanup_db):
    async with db_engine.acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'section name',
                'description': 'section description'
            })
        )
        post_id = await conn.scalar(
            insert(post).values({
                'section_id': section_id,
                'topic': 'post topic',
                'description': 'post description'
            })
        )
        await delete_post(conn, post_id)
        assert not await conn.scalar(
            select([exists().where(post.c.id == post_id)])
        )
