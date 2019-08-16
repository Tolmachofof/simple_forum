import logging.config
import pathlib

import click
import yaml
from aiohttp import web
from aiojobs.aiohttp import setup as setup_jobs
from aiopg.sa import create_engine

from simple_forum.routes import setup_routes


BASE_PATH = pathlib.Path(__file__).parent
# Путь до конфига по умолчанию
DEFAULT_CONFIG_PATH = BASE_PATH / 'conf' / 'local.yaml'


def read_config(config_path):
    with open(config_path) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


async def setup_db_engine(app):
    app['db'] = await create_engine(**app['config']['database'])
    app.on_cleanup.append(close_db_engine)


async def close_db_engine(app):
    app['db'].close()
    await app['db'].wait_closed()


def make_app(config):
    app = web.Application()
    app['config'] = config
    app.on_startup.append(setup_db_engine)
    setup_jobs(app)
    setup_routes(app)
    app.on_cleanup.append(close_db_engine)
    return app


@click.group()
@click.option(
    '--config',
    type=click.Path(exists=True, resolve_path=True),
    help='Path to config file'
)
@click.pass_context
def main(ctx, config):
    ctx.ensure_object(dict)
    config_path = config if config else DEFAULT_CONFIG_PATH
    ctx.obj['config'] = read_config(config_path)
    logging.config.dictConfig(ctx.obj['config']['logging'])


@main.command()
@click.pass_context
def run_app(ctx):
    app = make_app(ctx.obj['config'])
    web.run_app(app, **ctx.obj['config']['server'])


if __name__ == '__main__':
    main()
