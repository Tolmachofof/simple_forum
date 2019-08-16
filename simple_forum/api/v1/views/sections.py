import logging

from aiohttp import web
from aiojobs.aiohttp import atomic

from ....db.queries import (
    create_section, delete_section, find_sections, get_section,
    is_section_exist, update_section
)
from ...utils import load_data
from ..resources import SectionSchema, SectionsPageSchema

logger = logging.getLogger(__name__)


@atomic
async def create_section_view(request):
    schema = SectionSchema(strict=True)
    section_data = await load_data(request, schema)
    async with request.app['db'].acquire() as conn:
        new_section = await create_section(
            conn, section_data['name'], section_data['description']
        )
    response_data = schema.dump(new_section).data
    return web.json_response(response_data, status=201)


@atomic
async def update_section_view(request):
    schema = SectionSchema(strict=True)
    section_id = request.match_info['id']
    section_data = await load_data(request, schema)
    async with request.app['db'].acquire() as conn:
        if not await is_section_exist(conn, section_id):
            logger.error(
                'Cannot update section id {}. Section does not exist'.format(
                    section_id
                )
            )
            raise web.HTTPNotFound
        updated_section = await update_section(
            conn, section_id, name=section_data['name'],
            description=section_data['description']
        )
        response_data = schema.dump(updated_section).data
        return web.json_response(response_data)


async def retrieve_section_view(request):
    section_id = request.match_info['id']
    async with request.app['db'].acquire() as conn:
        section = await get_section(conn, section_id)
        if section is None:
            logger.error('Section id {} does not exist'.format(section_id))
            raise web.HTTPNotFound
    schema = SectionSchema()
    response_data = schema.dump(section).data
    return web.json_response(response_data)


async def retrieve_sections_view(request):
    schema = SectionsPageSchema()
    query_params = {
        param: request.query_params[param] for param in (
            'name__like', 'page_num', 'per_page'
        )
    }
    async with request.app['db'].acquire() as conn:
        sections_page = await find_sections(conn, **query_params)
    response_data = schema.dump(sections_page).data
    return web.json_response(response_data)


@atomic
async def delete_section_view(request):
    section_id = request.match_info['id']
    async with request.app['db'].acquire() as conn:
        if not await is_section_exist(conn, section_id):
            logger.error(
                'Cannot delete section id {}. Section does not exist'.format(
                    section_id
                )
            )
            raise web.HTTPNotFound
        await delete_section(conn, section_id)
        logger.info('Section id {} was successfully deleted.')
    return web.json_response(status=204)
