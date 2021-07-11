
import asyncio

from migrations.migrate import async_create_tables
from spiders.spider import get_cards_id


# 建表
# asyncio.run(async_create_tables())

# 获取所有卡片id
asyncio.run(get_cards_id())
