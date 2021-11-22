
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from models.dependencies import Base


class Card(Base):
    __tablename__ = "card"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, index=True, unique=True)
    name = Column(String(256), index=True, unique=True)
    text = Column(String(4096))
    supplement = Column(String(4096*2))
    supplement_date = Column(String(32), index=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # add this so that it can be accessed
    __mapper_args__ = {"eager_defaults": True}
