from marshmallow import Schema, fields
from marshmallow.validate import Length


class Page(Schema):
    
    page_num = fields.Integer(required=True, allow_none=False)
    per_page = fields.Integer(required=True, allow_none=False)
    total = fields.Integer(required=True, allow_none=False)
    
    
class SectionSchema(Schema):
    """Схема ресурса 'Раздел форума'."""
    
    id = fields.Integer(dump_only=True, required=True, allow_none=False)
    name = fields.String(
        required=True, allow_none=False, validate=Length(min=1)
    )
    description = fields.String(
        required=True, allow_none=False, validate=Length(min=1)
    )
    created_at = fields.DateTime(
        dump_only=True, format='%d.%m.%Y %H:%M:%S', required=True,
        allow_none=False
    )
    updated_at = fields.DateTime(
        dump_only=True, format='%d.%m.%Y %H:%M:%S', required=True
    )
    
    
class SectionsPageSchema(Page):
    
    items = fields.Nested(
        SectionSchema, many=True, required=True, allow_none=False
    )
    
    
class CommentSchema(Schema):

    id = fields.Integer(dump_only=True, required=True, allow_none=False)
    post_id = fields.Integer(required=True, allow_none=False)
    parent_id = fields.Integer(allow_none=True)
    text = fields.String(
        required=True, allow_none=False, validate=Length(min=1)
    )
    children = fields.List(fields.Integer(), dump_only=True, required=True)


class PostSchema(Schema):
    id = fields.Integer(dump_only=True, required=True, allow_none=False)
    section_id = fields.Integer(required=True, allow_none=False)
    topic = fields.String(required=True, allow_none=False)
    description = fields.String(required=True, allow_none=False)
    comments = fields.Nested(
        CommentSchema, many=True, dump_only=True, default=list
    )


class PostsPageSchema(Schema):
    items = fields.Nested(
        PostSchema, many=True, required=True, allow_none=False
    )
