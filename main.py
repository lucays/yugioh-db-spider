
import time
import asyncio

from spider import CardDBSpider
from rebuild import check_crete_tables


if __name__ == '__main__':
    while True:
        card_spider = CardDBSpider()
        asyncio.run(check_crete_tables())
        asyncio.run(card_spider.get_cards())
        time.sleep(3600*6)
