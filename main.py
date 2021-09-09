
import asyncio

from spider import CardDBSpider


if __name__ == '__main__':
    card_spider = CardDBSpider()
    asyncio.run(card_spider.get_cards())
