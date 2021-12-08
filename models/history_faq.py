from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from models.dependencies import Base


class HistoryFaq(Base):
    __tablename__ = "history_faq"

    id = Column(Integer, primary_key=True)
    faq_id = Column(Integer, index=True)
    title = Column(String(512))
    question = Column(String(4096))
    answer = Column(String(4096))
    tags = Column(String(128))
    date = Column(String(32), index=True)
    delete_flag = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # add this so that it can be accessed
    __mapper_args__ = {"eager_defaults": True}
