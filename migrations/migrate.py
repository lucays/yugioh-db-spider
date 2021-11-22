
from models import Card, CardFaq, HistoryCard, HistoryFaq, Faq
from models.dependencies import Base, engine


async def async_create_tables():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            Card.insert(), [{"name": "some name 1"}, {"name": "some name 2"}]
        )
    await engine.dispose()
