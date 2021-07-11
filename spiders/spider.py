import random
import asyncio

from requests_html import AsyncHTMLSession

from utils.session import AsyncSession
from configs.config import HEADERS
from configs.log_config import logger


async def get_per_page_cards_id(asession: AsyncHTMLSession, page: int, cards_id: list):
    """获取每一页的card id list

    Args:
        asession (AsyncHTMLSession): AsyncHTMLSession
        page (int): 页数
        cards_id (list): card id list
    """
    card_page_url = f'https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&sess=1&page={page}&mode=2&stype=1&othercon=2&rp=100&request_locale=ja'
    if HEADERS['referer']:
        HEADERS['referer'] = f'https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&sess=3&page={page-1}&mode=2&stype=1&othercon=2&rp=100'
    else:
        HEADERS['referer'] = 'https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&sess=3&page=2&mode=2&stype=1&othercon=2&rp=100'
    r = await asession.get(card_page_url, headers=HEADERS)
    await r.html.arender(sleep=random.randrange(1, 2))
    count = r.html.xpath('//*[@id="article_body"]/table/tbody/tr/td/div[1]/div/strong//text()')[0].strip()
    logger.info(count)
    cards_url = r.html.xpath('//*[@id="search_result"]//input/@value')
    current_page_cards_id = [i.split('cid=')[1] for i in cards_url]
    if current_page_cards_id:
        cards_id.extend(current_page_cards_id)
        await get_per_page_cards_id(asession, page+1, cards_id)
    logger.info(page, len(cards_id))

async def get_cards_id():
    async with AsyncSession() as asession:
        card_start_page = 1
        cards_id = []
        await get_per_page_cards_id(asession, card_start_page, cards_id)
        # TODO 存储cards id


async def get_card_info(asession: AsyncHTMLSession, card_id: str, page: int = 1):
    """获取卡片详情数据

    Args:
        asession (AsyncHTMLSession): AsyncHTMLSession
        card_id (str): card id
        page (int): faq page
    """
    card_info_url = f'https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&sort=2&page={page}&request_locale=ja'
    HEADERS['referer'] = f'https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&request_locale=ja'
    r = await asession.get(card_info_url, headers=HEADERS)
    await r.html.arender(sleep=random.randrange(1, 2))
    card_name = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')[0]
    card_text = r.html.xpath('//*[@id="card_text"]/text()')[0]
    card_supplement = r.html.xpath('//*[@id="supplement"]//text()')
    card_supplement_date = r.html.xpath('//*[@id="update_time"]/div/span/text()')[0]
    current_page_card_faq_links = [f'https://www.db.yugioh-card.com/{i}' for i in r.html.xpath('//div[@class="f_left qa_title"]/input/@value')]
    if current_page_card_faq_links:
        # TODO 没有必要获取所有card id或者faq link后再请求，可以考虑拿到一个就请求一个利用协程
        # https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid=10588&sort=2&page=2
        pass


async def get_cards_info(cards_id: list):
    async with AsyncSession() as asession:
        for card_id in cards_id:
            card_info_url = f'https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&request_locale=ja'
            

# asyncio.run(get_cards_id())
