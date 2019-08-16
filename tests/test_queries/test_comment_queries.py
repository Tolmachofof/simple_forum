import random
from datetime import datetime
from unittest import mock

import pytest
from sqlalchemy import ColumnDefault, and_, exists, insert, select

from simple_forum.db.models import comment, post, section
from simple_forum.db.queries import (
    create_comment, delete_comment, get_comment, get_post_comments
)


async def test_create_comment(db_engine, cleanup_db):
    comment_text = 'comment text'
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
            comment.c.created_at, 'default',
            new=ColumnDefault(lambda: dt_now)
        ):
            new_comment = await create_comment(conn, post_id, comment_text)
            assert new_comment is not None
            assert new_comment.post_id == post_id
            assert new_comment.text == comment_text
            assert new_comment.parent_id is None
            assert new_comment.created_at == dt_now
            assert await conn.scalar(
                select([exists().where(
                    and_(
                        comment.c.id == new_comment.id,
                        comment.c.post_id == post_id,
                        comment.c.text == comment_text,
                        comment.c.created_at == dt_now
                    )
                )])
            )
            

async def test_create_child_comment(db_engine, cleanup_db):
    comment_text = 'comment text'
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
        parent_id = await conn.scalar(
            insert(comment).values({'post_id': post_id, 'text': comment_text})
        )
        with mock.patch.object(
            comment.c.created_at, 'default',
            new=ColumnDefault(lambda: dt_now)
        ):
            new_comment = await create_comment(
                conn, post_id, comment_text, parent_id=parent_id
            )
            assert new_comment is not None
            assert new_comment.post_id == post_id
            assert new_comment.text == comment_text
            assert new_comment.parent_id == parent_id
            assert new_comment.created_at == dt_now
            assert await conn.scalar(
                select([exists().where(
                    and_(
                        comment.c.id == new_comment.id,
                        comment.c.post_id == post_id,
                        comment.c.text == comment_text,
                        comment.c.created_at == dt_now,
                        comment.c.parent_id == parent_id
                    )
                )])
            )


async def test_get_comment(db_engine, cleanup_db):
    comment_text = 'comment text'
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
        comment_id = await conn.scalar(
            insert(comment).values({'post_id': post_id, 'text': comment_text})
        )
        _comment = await get_comment(conn, comment_id)
        assert _comment is not None
        assert _comment.id == comment_id
        assert _comment.text == comment_text
        

async def test_get_comment_if_comment_does_not_exist(db_engine):
    async with db_engine.acquire() as conn:
        assert await get_comment(conn, random.randint(1, 100)) is None
        

async def test_get_post_comments(db_engine, cleanup_db):
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
        parent_id = await conn.scalar(
            insert(comment).values({
                'post_id': post_id,
                'text': 'comment text'
            })
        )
        child_id = await conn.scalar(
            insert(comment).values({
                'post_id': post_id,
                'parent_id': parent_id,
                'text': 'comment text'
            })
        )
        post_comments = await get_post_comments(conn, post_id)
        parent_comment, child_comment = sorted(
            post_comments, key=lambda item: item.id
        )
        assert parent_comment.id == parent_id
        assert parent_comment.parent_id is None
        assert parent_comment.children == [child_id]
        assert child_comment.id == child_id
        assert child_comment.parent_id == parent_id
        assert child_comment.children == []


async def test_delete_comment(db_engine, cleanup_db):
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
        comment_id = await conn.scalar(
            insert(comment).values({
                'post_id': post_id,
                'text': 'comment text'
            })
        )
        await delete_comment(conn, comment_id)
        assert not await conn.scalar(
            select([exists().where(comment.c.id == comment_id)])
        )
