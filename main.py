import time
import asyncio

from configs.log_config import logger
from spider import CardDBSpider
from rebuild import async_create_tables


if __name__ == "__main__":
    while True:
        logger.info("start spider...")
        a = time.time()
        card_spider = CardDBSpider()
        asyncio.run(async_create_tables())
        asyncio.run(card_spider.get_cards())
        logger.info(f"spider end. cost time: {time.time()-a}, sleep...")
        time.sleep(3600*5)
