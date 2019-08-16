from collections import namedtuple
from functools import partial
from typing import NewType, Optional

from aiopg.sa import SAConnection
from aiopg.sa.result import RowProxy
from sqlalchemy import (
    Table, alias, delete, desc, exists, func, insert, select, update
)

from .models import comment, post, section

DEFAULT_PAGE_NUM = 1
DEFAULT_PER_PAGE = 25


SectionRow = NewType('SectionRow', RowProxy)
PostRow = NewType('PostRow', RowProxy)
CommentRow = NewType('CommentRow', RowProxy)


Page = namedtuple('Page', ('items', 'page_num', 'per_page', 'total'))


SectionsPage = NewType('SectionsPage', Page)
PostsPage = NewType('PostsPage', Page)


async def is_exist(model: Table, conn: SAConnection, obj_id: int) -> bool:
    return await conn.scalar(select([exists().where(model.c.id == obj_id)]))


is_section_exist = partial(is_exist, section)
is_post_exist = partial(is_exist, post)
is_comment_exist = partial(is_exist, comment)


async def delete_obj(model: Table, conn: SAConnection, obj_id: int) -> None:
    return await conn.execute(delete(model).where(model.c.id == obj_id))


delete_section = partial(delete_obj, section)
delete_post = partial(delete_obj, post)
delete_comment = partial(delete_obj, comment)


async def create_section(
    conn: SAConnection, name: str, description: str
) -> SectionRow:
    """Создание нового раздела форума.
    
    :param conn: коннект к БД.
    :param name: название раздела.
    :param description: описание раздела."""
    section_id = await conn.scalar(
        insert(section).values({
            'name': name,
            'description': description
        })
    )
    return await get_section(conn, section_id)


async def update_section(
    conn: SAConnection, section_id: int, name: Optional[str] = None,
    description: Optional[str] = None
) -> SectionRow:
    """Обновление информации о разделе форума.
    
    :param conn: коннект к БД.
    :param section_id: id раздела.
    :param name: название раздела.
    :param description: описание раздела."""
    for_update = {}
    if name is not None:
        for_update['name'] = name
    if description is not None:
        for_update['description'] = description
    if for_update:
        await conn.execute(
            update(section).where(
                section.c.id == section_id
            ).values(for_update)
        )
    return await get_section(conn, section_id)
    

async def get_section(
    conn: SAConnection, section_id: int
) -> Optional[SectionRow]:
    """Возвращает раздел форума с переданным id.
    Если раздела не существует - возвращает None
    
    :param conn: коннект к БД.
    :param section_id: id раздела."""
    cur = await conn.execute(
        select([section]).where(section.c.id == section_id)
    )
    return await cur.fetchone()


async def find_sections(
    conn: SAConnection, name__like: Optional[str] = None,
    page_num: int = DEFAULT_PAGE_NUM, per_page: int = DEFAULT_PER_PAGE
) -> SectionsPage:
    """Возвращает страницу пагинации, содержащую разделы форума.
    
    :param conn: коннект к БД.
    :param name__like: шаблон для поиска разделов по названию.
    :param page_num: номер страницы.
    :param per_page: количество элементов на странице."""
    query = select([section]).order_by(
        desc(section.c.created_at), desc(section.c.updated_at)
    )
    if name__like is not None:
        query = query.where(section.c.name.ilike(name__like))
    return await _paginate_query(
        conn, query, page_num=page_num, per_page=per_page
    )


async def create_post(
    conn: SAConnection, section_id: int, topic: str, description: str
) -> PostRow:
    """Создание нового поста в разделе.
    
    :param conn: коннект к БД.
    :param section_id: id раздела.
    :param topic: тема поста.
    :param description: описание поста."""
    post_id = await conn.scalar(
        insert(post).values({
            'section_id': section_id,
            'topic': topic,
            'description': description
        })
    )
    return await get_post(conn, post_id)


async def update_post(
    conn: SAConnection, post_id: int, topic: Optional[str] = None,
    description: Optional[str] = None
) -> PostRow:
    """Обновление информации о посте.
    
    :param conn: коннект к БД.
    :param post_id: id поста.
    :param topic: тема поста.
    :param description: описание поста."""
    for_update = {}
    if topic is not None:
        for_update['topic'] = topic
    if description is not None:
        for_update['description'] = description
    if for_update:
        await conn.execute(
            update(post).where(
                post.c.id == post_id
            ).values(for_update)
        )
    return await get_post(conn, post_id)


async def get_post(conn: SAConnection, post_id: int) -> Optional[PostRow]:
    """Возвращает пост с переданным id.
    Если пост не существует - возвращает None
    
    :param conn: коннект к БД.
    :param post_id: id поста."""
    cur = await conn.execute(select([post]).where(post.c.id == post_id))
    return await cur.fetchone()


async def find_posts(
    conn: SAConnection, topic__like: Optional[str],
    page_num: int = DEFAULT_PAGE_NUM, per_page: int = DEFAULT_PER_PAGE
) -> PostsPage:
    """Возвращает страницу пагинации, содержащую посты.

    :param conn: коннект к БД.
    :param topic__like: шаблон для поиска разделов по названию.
    :param page_num: номер страницы.
    :param per_page: количество элементов на странице."""
    query = select([section]).order_by(
        desc(section.c.created_at), desc(section.c.updated_at)
    )
    if topic__like is not None:
        query = query.where(section.c.name.ilike(topic__like))
    return await _paginate_query(
        conn, query, page_num=page_num, per_page=per_page
    )


async def create_comment(
    conn: SAConnection, post_id: int, text: str,
    parent_id: Optional[int] = None
) -> CommentRow:
    """Создает комментарий к посту.
    
    :param conn: коннект к БД.
    :param post_id: id поста, к которому добавляется комментарий.
    :param text: текст комментария.
    :param parent_id: id родительского комментария
    (в случае цепочки комментариев)"""
    comment_id = await conn.scalar(
        comment.insert().values({
            'post_id': post_id,
            'text': text,
            'parent_id': parent_id,
            
        })
    )
    return await get_comment(conn, comment_id)


async def update_comment(
    conn: SAConnection, comment_id: int, text: str
) -> CommentRow:
    """Обноовляет текст комментария к посту.
    
    :param conn: коннект к БД.
    :param comment_id: id комментария.
    :param text: новый текст комментария.
    """
    await conn.execute(
        update(comment).where(comment.c.id == comment_id).values({
            'text': text
        })
    )
    return await get_comment(conn, comment_id)
    
    
async def get_comment(
    conn: SAConnection, comment_id: int
) -> Optional[CommentRow]:
    """Возвращает комментарий по id.
    Если комментария не существует - возвращает None.
    
    :param conn: коннект к БД.
    :param comment_id: id комментария."""
    cur = await conn.execute(
        select([comment]).where(comment.c.id == comment_id)
    )
    return await cur.fetchone()


async def get_post_comments(conn: SAConnection, post_id: int):
    """Возвращает все комментарии к посту.
    
    :param conn: коннект к БД.
    :param post_id: id поста.
    """
    children = alias(comment, 'children')
    cur = await conn.execute(
        select([
            comment,
            func.array_remove(
                func.array_agg(children.c.id), None
            ).label('children')
        ]).select_from(
            comment.join(
                children, comment.c.id == children.c.parent_id, isouter=True
            )
        ).where(
            comment.c.post_id == post_id
        ).group_by(comment.c.id)
    )
    return await cur.fetchall()
    
    
async def _paginate_query(
    conn, query, page_num=DEFAULT_PAGE_NUM, per_page=DEFAULT_PER_PAGE
) -> Page:
    total = await conn.scalar(
        select([func.count('id')]).select_from(alias(query, 'query'))
    )
    cur = await conn.execute(query.offset(page_num).limit(per_page))
    items = await cur.fetchall()
    return Page(items, page_num, per_page, total)
