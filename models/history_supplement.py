from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from models.dependencies import Base


class HistorySupplement(Base):
    __tablename__ = "history_supplement"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, index=True)
    name = Column(String(128), index=True)
    supplement = Column(String(4096))
    supplement_date = Column(String(20), index=True)
    effect = Column(String(1024))
    p_effect = Column(String(1024))
    p_supplement = Column(String(4096))
    p_supplement_date = Column(String(20), index=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # add this so that it can be accessed
    __mapper_args__ = {"eager_defaults": True}
