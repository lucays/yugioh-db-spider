
import time
import asyncio

from spider import CardDBSpider


if __name__ == '__main__':
    while True:
        card_spider = CardDBSpider()
        asyncio.run(card_spider.get_cards())
        time.sleep(3600*6)
