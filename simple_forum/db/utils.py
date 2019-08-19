import asyncio
from time import sleep

from aiopg.sa import create_engine as _create_async_engine
from psycopg2 import OperationalError as AiopgOperationalError
from sqlalchemy import create_engine as _create_blocking_engine
from sqlalchemy.exc import OperationalError as AlchemyOperationalError

BASE_TIMEOUT = 0.01
MAX_RECONNECTS = 10


async def create_async_engine(
    db_config, base_timeout=BASE_TIMEOUT, max_reconnects=MAX_RECONNECTS
):
    error = None
    delay = base_timeout
    for _ in range(max_reconnects):
        try:
            return await _create_async_engine(**db_config)
        except AiopgOperationalError as exc:
            error = exc
            await asyncio.sleep(delay)
            delay *= 2
    raise error


async def close_async_engine(engine):
    engine.close()
    await engine.wait_closed()


def create_blocking_engine(
    dsn, base_timeout=BASE_TIMEOUT, max_reconnects=MAX_RECONNECTS
):
    error = None
    delay = base_timeout
    for _ in range(max_reconnects):
        try:
            return _create_blocking_engine(dsn, isolation_level='AUTOCOMMIT')
        except AlchemyOperationalError as exc:
            error = exc
            sleep(delay)
            delay *= 2
    raise error


def close_blocking_engine(engine):
    engine.close()
