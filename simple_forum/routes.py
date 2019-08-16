from aiohttp import web

from .api.v1.views.sections import (
    create_section_view, retrieve_section_view, retrieve_sections_view,
    update_section_view, delete_section_view
)
from .api.v1.views.posts import (
    create_post_view, retrieve_post_view, retrieve_posts_view,
    update_post_view, delete_post_view
)
from .api.v1.views.comments import (
    create_comment_view, update_comment_view, delete_comment_view
)


SECTION_URLS = (
    web.post(r'/api/v1/sections', create_section_view),
    web.get(r'/api/v1/sections', retrieve_sections_view),
    web.get(r'/api/v1/sections/{id:\d+}', retrieve_section_view),
    web.put(r'/api/v1/sections/{id:\d+}', update_section_view),
    web.delete(r'/api/v1/sections/{id:\d+}', delete_section_view)
)


POST_URLS = (
    web.post(r'/api/v1/posts', create_post_view),
    web.get(r'/api/v1/posts', retrieve_posts_view),
    web.get(r'/api/v1/posts/{id:\d+}', retrieve_post_view),
    web.put(r'/api/v1/posts/{id:\d+}', update_post_view),
    web.delete(r'/api/v1/posts/{id:\d+}', delete_post_view)
)


COMMENT_URLS = (
    web.post(r'/api/v1/comments', create_comment_view),
    web.put(r'/api/v1/comments/{id:\d+}', update_comment_view),
    web.delete(r'/api/v1/comments/{id:\d+}', delete_comment_view)
)


URLS = (
    *SECTION_URLS,
    *POST_URLS,
    *COMMENT_URLS
)


def setup_routes(app):
    app.add_routes(URLS)
