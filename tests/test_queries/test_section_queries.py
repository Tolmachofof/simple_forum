import random
from datetime import datetime
from unittest import mock

from sqlalchemy import ColumnDefault, and_, exists, insert, select

from simple_forum.db.models import section
from simple_forum.db.queries import (
    create_section, delete_section, get_section, is_section_exist,
    update_section
)


async def test_create_section(db_engine, cleanup_db):
    section_name = 'section name'
    section_description = 'section description'
    dt_now = datetime.utcnow()
    async with db_engine.acquire() as conn:
        with mock.patch.object(
            section.c.created_at, 'default',
            new=ColumnDefault(lambda: dt_now)
        ):
            new_section = await create_section(
                conn, section_name, section_description
            )
        assert new_section.name == section_name
        assert new_section.description == section_description
        assert new_section.created_at == dt_now
        assert await conn.scalar(
            select([exists().where(
                and_(
                    section.c.id == new_section.id,
                    section.c.name == new_section.name,
                    section.c.description == new_section.description,
                    section.c.created_at == new_section.created_at
                )
            )])
        )
        
        
async def test_is_section_exist(db_engine, cleanup_db):
    async with db_engine.acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'section name',
                'description': 'section description'
            })
            
        )
        assert await is_section_exist(conn, section_id)
        

async def test_is_section_exist_if_section_does_not_exist(db_engine):
    async with db_engine.acquire() as conn:
        assert not await is_section_exist(conn, random.randint(1, 100))
        

async def test_get_section(db_engine, cleanup_db):
    section_name = 'section name'
    section_description = 'section description'
    dt_now = datetime.utcnow()
    async with db_engine.acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': section_name,
                'description': section_description,
            })
        )
        _section = await get_section(conn, section_id)
        assert _section is not None
        assert _section.id == section_id
        assert _section.name == section_name
        assert _section.description == section_description
        

async def test_get_section_if_section_does_not_exist(db_engine):
    async with db_engine.acquire() as conn:
        assert await get_section(conn, random.randint(1, 100)) is None
    

async def test_update_section(db_engine, cleanup_db):
    section_data = {
        'name': 'section name',
        'description': 'section description'
    }
    async with db_engine.acquire() as conn:
        section_id = await conn.scalar(insert(section).values(section_data))
        new_name = 'new section name'
        new_description = 'new section description'
        dt_now = datetime.utcnow()
        with mock.patch.object(
            section.c.updated_at, 'default',
            new=ColumnDefault(lambda: dt_now)
        ):
            updated_section = await update_section(
                conn, section_id, name=new_name, description=new_description
            )
            assert updated_section is not None
            assert updated_section.name == new_name
            assert updated_section.description == new_description
            assert updated_section.updated_at == dt_now
            assert await conn.scalar(
                select([exists().where(
                    and_(
                        section.c.id == section_id,
                        section.c.name == new_name,
                        section.c.description == new_description,
                        section.c.updated_at == dt_now
                    )
                )])
            )


async def test_delete_section(db_engine, cleanup_db):
    async with db_engine.acquire() as conn:
        section_id = await conn.scalar(
            insert(section).values({
                'name': 'section name',
                'description': 'section description'
            })
        )
        await delete_section(conn, section_id)
        assert not await conn.scalar(
            select([exists().where(section.c.id == section_id)])
        )
