
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from models.dependencies import Base


class HistoryCard(Base):
    __tablename__ = "history_card"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, index=True)
    name = Column(String(256), index=True)
    attr = Column(String(24))
    level = Column(String(10))
    rank = Column(String(10))
    link_rating = Column(String(10))
    p_scale = Column(String(10))
    p_effect = Column(String(1024))
    type_ = Column(String(24))
    monster_types = Column(String(128))
    attack = Column(String(10))
    defense = Column(String(10))
    text = Column(String(1024))
    supplement = Column(String(4096))
    supplement_date = Column(String(20), index=True)
    p_supplement = Column(String(4096))
    p_supplement_date = Column(String(20), index=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # add this so that it can be accessed
    __mapper_args__ = {"eager_defaults": True}
