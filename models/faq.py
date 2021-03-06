from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from models.dependencies import Base


class Faq(Base):
    __tablename__ = "faq"

    id = Column(Integer, primary_key=True)
    faq_id = Column(Integer, index=True, unique=True)
    title = Column(String(512))
    question = Column(String(4096))
    answer = Column(String(4096))
    tags = Column(String(128))
    date = Column(String(32), index=True)
    count = Column(Integer, default=0)
    delete_flag = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # add this so that it can be accessed
    __mapper_args__ = {"eager_defaults": True}
