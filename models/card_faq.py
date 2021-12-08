from datetime import datetime

from sqlalchemy import Column, DateTime, Integer

from models.dependencies import Base


class CardFaq(Base):
    __tablename__ = "card_faq"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, index=True)
    faq_id = Column(Integer, index=True)
    delete_flag = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # add this so that it can be accessed
    __mapper_args__ = {"eager_defaults": True}
