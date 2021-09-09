
import random
from typing import Callable

from utils.session import AsyncSession
from configs import HEADERS
from configs.log_config import logger


class CardDBSpider:

    def __init__(self) -> None:
        self.prefix = 'https://www.db.yugioh-card.com/yugiohdb'
        self.fail_url = []

    async def get_and_render(self, asession, url: str, headers: dict, func: Callable):
        try:
            r = await asession.get(url, headers=headers)
            await r.html.arender(sleep=random.randrange(1, 2))
            return r
        except:
            self.fail_url.append((url, func))
            return None

    async def retry(self, asession):
        # self.fail_url应该存redis等地方，定时轮询
        while self.fail_url:
            url, func = self.fail_url.pop()
            await func(asession, url)

    async def get_cards(self):
        async with AsyncSession() as asession:
            start_page = 1
            start_card_page_url = f'{self.prefix}/card_search.action?ope=1&sess=1&page={start_page}&mode=2&stype=1&othercon=2&rp=100&request_locale=ja'
            await self.get_per_page_cards_id(asession, start_card_page_url)

    async def get_per_page_cards_id(self, asession, card_page_url: str):
        page = card_page_url.split('&page=')[1].split('&')[0]
        if HEADERS['referer']:
            HEADERS['referer'] = f'{self.prefix}/card_search.action?ope=1&sess=3&page={page-1}&mode=2&stype=1&othercon=2&rp=100'
        else:
            HEADERS['referer'] = f'{self.prefix}/card_search.action?ope=1&sess=3&page=2&mode=2&stype=1&othercon=2&rp=100'
        r = await self.get_and_render(asession, card_page_url, HEADERS)
        if not r:
            return
        cards_url = r.html.xpath('//*[@id="search_result"]//input/@value')
        for card_url in cards_url:
            card_id = card_url.split('cid=')[1]
            card_url = f'https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&sort=2&page=1&request_locale=ja'
            await self.get_card_info(asession, card_url)
        if cards_url:
            next_page_url = f'{self.prefix}/card_search.action?ope=1&sess=1&page={page+1}&mode=2&stype=1&othercon=2&rp=100&request_locale=ja'
            await self.get_per_page_cards_id(asession, next_page_url)

    async def get_card_info(self, asession, card_url: str):
        """获取卡片详情数据

        Args:
            asession :
            card_id (str): card id
            page (int): faq page
        """
        page = card_url.split('&page=')[1].split('&')[0]
        card_id = card_url.split('cid=')[1].split('&')[0]
        HEADERS['referer'] = f'https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&request_locale=ja'
        r = await self.get_and_render(asession, card_url, HEADERS)
        if not r:
            return
        card_name = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')[0].strip()
        card_text = r.html.xpath('//*[@id="card_text"]/text()')[0].strip().replace('「\n', '「').replace('\n」', '」')
        card_supplement = '\n'.join(r.html.xpath('//*[@id="supplement"]//text()')).strip().replace('「\n', '「').replace('\n」', '」')
        card_supplement_date = r.html.xpath('//*[@id="update_time"]/div/span/text()')[0]
        part_urls = r.html.xpath('//div[@class="f_left qa_title"]/input/@value')
        print(card_id, card_name, card_supplement_date)
        print(card_text)
        print(card_supplement)
        for part_url in part_urls:
            faq_url = f'https://www.db.yugioh-card.com/{part_url}&request_locale=ja'
            await self.get_faq_info(asession, faq_url)
        if part_urls:
            next_page_url = f'https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&sort=2&page={page+1}&request_locale=ja'
            await self.get_card_info(asession, next_page_url)

    async def get_faq_info(self, asession, faq_url: str):
        faq_id = faq_url.split('fid=')[1].split('&')[0]
        r = await self.get_and_render(asession, faq_url, HEADERS)
        if not r:
            return
        title = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')[0]
        question = '\n'.join(r.html.xpath('//*[@id="question_text"]//text()')).strip().replace('「\n', '「').replace('\n」', '」')
        answer = '\n'.join(r.html.xpath('//*[@id="answer_text"]//text()')).strip().replace('「\n', '「').replace('\n」', '」')
        tags = r.html.xpath('//*[@id="tag_update"]/div/span[@class="f_left tag_name"]/text()')
        date = r.html.xpath('//*[@id="tag_update"]/div/span[@class="f_right"]/text()')[0]
        print(title)
        print(answer)
        print(tags, date)
