from models.dependencies import Base, engine


async def async_create_tables():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == '__main__':
    from migrations.migrate import async_create_tables
    import asyncio
    asyncio.run(async_create_tables())
