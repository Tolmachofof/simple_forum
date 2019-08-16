from datetime import datetime

from sqlalchemy import (
    Column, ColumnDefault, DateTime, ForeignKey, Integer, MetaData, String,
    Table
)

meta = MetaData()


# Раздел форума
section = Table(
    'section',
    meta,
    
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('description', String),
    Column('created_at', DateTime, default=ColumnDefault(datetime.utcnow)),
    Column('updated_at', DateTime, onupdate=ColumnDefault(datetime.utcnow))
)


# Пост
post = Table(
    'post',
    meta,
    
    Column('id', Integer, primary_key=True),
    Column('section_id', ForeignKey('section.id', ondelete='CASCADE')),
    Column('topic', String),
    Column('description', String),
    Column('created_at', DateTime, default=ColumnDefault(datetime.utcnow)),
    Column('updated_at', DateTime, onupdate=ColumnDefault(datetime.utcnow))
)


# Комментарий к посту
comment = Table(
    'comment',
    meta,
    
    Column('id', Integer, primary_key=True),
    Column('post_id', ForeignKey('post.id', ondelete='CASCADE')),
    Column('parent_id', ForeignKey('comment.id', ondelete='CASCADE')),
    Column('text', String),
    Column('created_at', DateTime, default=ColumnDefault(datetime.utcnow)),
    Column('updated_at', DateTime, onupdate=ColumnDefault(datetime.utcnow))
)
