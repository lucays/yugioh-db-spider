
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from models.dependencies import Base


class Card(Base):
    __tablename__ = "card"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, index=True, unique=True)
    name = Column(String(256), index=True, unique=True)
    attr = Column(String(24))
    level = Column(String(10))
    rank = Column(String(10))
    link_rating = Column(String(10))
    p_scale = Column(String(10))
    type_ = Column(String(24))
    monster_types = Column(String(128))
    attack = Column(String(10))
    defense = Column(String(10))
    src_url = Column(String(256))
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # add this so that it can be accessed
    __mapper_args__ = {"eager_defaults": True}
