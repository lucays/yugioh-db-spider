
import asyncio

from spider import CardDBSpider


if __name__ == '__main__':
    card_spider = CardDBSpider()
    asyncio.run(card_spider.get_cards())
    # from migrations.migrate import async_create_tables
    # import asyncio
    # asyncio.run(async_create_tables())
