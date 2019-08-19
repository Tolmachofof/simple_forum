import logging.config

from aiohttp import web
from aiojobs.aiohttp import setup as setup_jobs

from simple_forum.utils import read_config
from simple_forum.db.utils import create_async_engine, close_async_engine
from simple_forum.routes import setup_routes


async def setup_db_engine(app):
    app['db'] = await create_async_engine(app['config']['database'])
    app.on_cleanup.append(close_db_engine)


async def close_db_engine(app):
    await close_async_engine(app['db'])


def make_app(config):
    app = web.Application()
    app['config'] = config
    app.on_startup.append(setup_db_engine)
    setup_jobs(app)
    setup_routes(app)
    return app


def run(config):
    app = make_app(config)
    web.run_app(app, **config['server'])


if __name__ == '__main__':
    config = read_config()
    logging.config.dictConfig(config['logging'])
    run(config)
