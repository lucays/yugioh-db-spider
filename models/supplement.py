from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from models.dependencies import Base


class Supplement(Base):
    __tablename__ = "supplement"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, index=True, unique=True)
    name = Column(String(128), index=True, unique=True)
    supplement = Column(String(4096))
    supplement_date = Column(String(20), index=True)
    effect = Column(String(1024))
    p_effect = Column(String(1024))
    p_supplement = Column(String(4096))
    p_supplement_date = Column(String(20), index=True)
    count = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # add this so that it can be accessed
    __mapper_args__ = {"eager_defaults": True}
