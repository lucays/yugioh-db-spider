from sqlalchemy.sql.expression import select

from models import Card
from models.dependencies import Base, engine, async_session


async def async_create_tables():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def check_crete_tables():
    need_rebuild = True
    async with async_session() as session:
        async with session.begin():
            cards = await session.execute(select(Card).limit(1))
            card = cards.scalars().first()
            if card:
                need_rebuild = False
    if need_rebuild:
        await async_create_tables()


if __name__ == '__main__':
    import asyncio
    asyncio.run(async_create_tables())
