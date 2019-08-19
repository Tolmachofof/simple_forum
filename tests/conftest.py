import asyncio

import pytest
from sqlalchemy import delete

from simple_forum.db.models import section
from simple_forum.db.utils import close_async_engine, create_async_engine
from simple_forum.utils import DEFAULT_CONFIG_PATH, read_config


def pytest_addoption(parser):
    parser.addoption(
        '--config', action='store', default=DEFAULT_CONFIG_PATH,
        help='Configuration path'
    )


@pytest.fixture(scope='session')
def config_path(request):
    return request.config.getoption('--config')


@pytest.yield_fixture(scope='session')
def config(config_path):
    yield read_config(config_path)
    
    
@pytest.yield_fixture(scope='session')
def loop():
    _loop = asyncio.get_event_loop_policy().new_event_loop()
    yield _loop
    _loop.close()
    

@pytest.yield_fixture(scope='session')
async def db_engine(loop, config):
    engine = await create_async_engine(config['database'])
    yield engine
    await close_async_engine(engine)
    
    
@pytest.yield_fixture
async def cleanup_db(loop, db_engine):
    yield
    async with db_engine.acquire() as conn:
        await conn.execute(delete(section))
