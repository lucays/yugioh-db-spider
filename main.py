
import time
import asyncio

from configs.log_config import logger
from spider import CardDBSpider
from rebuild import async_create_tables


if __name__ == '__main__':
    # TODO
    # 卡片详情不重复爬取，如果卡片说明有修改，或者qa有更新，才会再次爬取卡片详情
    # 卡片详情和卡片说明分表
    # 比对每张卡的faq数据是否与上次一致，如果变少了说明有删除
    # 比对每张卡的faq日期，如果与已有的一致，不再爬取
    # 添加点击数列，默认0
    while True:
        logger.info('start spider...')
        card_spider = CardDBSpider()
        asyncio.run(async_create_tables())
        asyncio.run(card_spider.get_cards())
        logger.info('sleep...')
        time.sleep(3600*6)
