import asyncio
import pathlib

import pytest
import yaml
from aiopg.sa import create_engine
from sqlalchemy import delete

from simple_forum.db.models import section

CONFIG_PATH = pathlib.Path(__file__).parent.parent / 'conf' / 'testing.yaml'


def pytest_addoption(parser):
    parser.addoption(
        '--config', action='store', default=CONFIG_PATH,
        help='Configuration path'
    )


@pytest.fixture(scope='session')
def config_path(request):
    return request.config.getoption('--config')


@pytest.yield_fixture(scope='session')
def config(config_path):
    with open(config_path) as f:
        conf = yaml.load(f, Loader=yaml.BaseLoader)
    yield conf
    
    
@pytest.yield_fixture
async def db_engine(loop, config):
    engine = await create_engine(**config['database'])
    yield engine
    engine.close()
    await engine.wait_closed()
    
    
@pytest.yield_fixture
async def cleanup_db(loop, db_engine):
    yield
    async with db_engine.acquire() as conn:
        await conn.execute(delete(section))
