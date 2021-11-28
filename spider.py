import random
import traceback
from typing import Callable

from utils.session import AsyncSession
from configs import HEADERS
from configs.log_config import logger
from pipeline import save_card, save_faq


class CardDBSpider:
    def __init__(self) -> None:
        self.prefix = "https://www.db.yugioh-card.com/yugiohdb"
        self.fail_ids = {
            'card': set(),
            'faq': set(),
            'card_page': set(),
            'card_faq_page': set(),
        }
        self.funcs = {
            'card': self.get_card_supplement_info,
            'faq': self.get_faq_info,
            'card_page': self.get_per_page_cards_id,
            'card_faq_page': self.get_card_faq_page
        }
        self.success_ids = {
            'card': set(),
            'faq': set(),
            'card_page': set(),
            'card_faq_page': set(),
        }

    async def get_and_render(self, asession, url: str, headers: dict, func: Callable):
        try:
            r = await asession.get(url, headers=headers)
            await r.html.arender(retries=3, sleep=random.uniform(0.9, 1.5), timeout=15)
            return r
        except Exception:
            logger.exception(f'request url: {url} fail, func: {func}, error: {traceback.format_exc()}')
            return None

    async def retry(self, asession):
        for type_, values in self.fail_ids.items():
            if values in self.success_ids[type_]:
                self.fail_ids[type_].remove(values)
                continue
            if type_ == 'card_faq_page':
                for value in values:
                    card_id, page = value
                    await self.funcs[type_](asession, card_id, page)
            else:
                for value in values:
                    await self.funcs[type_](asession, value)

    async def get_cards(self):
        async with AsyncSession() as asession:
            start_page = 1
            await self.get_per_page_cards_id(asession, start_page)

    async def get_per_page_cards_id(self, asession, page: int):
        card_page_url = f"{self.prefix}/card_search.action?ope=1&sess=1&page={page}&mode=2&stype=1&othercon=2&rp=100&request_locale=ja"
        if HEADERS["referer"]:
            HEADERS["referer"] = f"{self.prefix}/card_search.action?ope=1&sess=3&page={page-1}&mode=2&stype=1&othercon=2&rp=100"
        else:
            HEADERS["referer"] = f"{self.prefix}/card_search.action?ope=1&sess=3&page=2&mode=2&stype=1&othercon=2&rp=100"
        if page in self.success_ids['card_page']:
            return None
        r = await self.get_and_render(asession, card_page_url, HEADERS, self.get_per_page_cards_id)
        if not r:
            self.fail_ids['card_page'].add(page)
            await self.retry(asession)
            return None
        cards_url = r.html.xpath('//*[@id="search_result"]//input/@value')
        if cards_url:
            self.success_ids['card_page'].add(page)
            logger.warning(f'card page: {page} fetched')
            for card_url in cards_url:
                card_id = int(card_url.split("cid=")[1])
                try:
                    await self.get_card_supplement_info(asession, card_id)
                except Exception:
                    logger.exception(f'some error occured: {traceback.format_exc()}')
        else:
            self.fail_ids['card_page'].add(page)
            await self.get_per_page_cards_id(asession, page+1)
        pages = r.html.xpath('//div[@class="page_num"]/span/a/text()')
        if pages and pages[-1] == '»':
            await self.get_per_page_cards_id(asession, page+1)

    async def get_card_info(self, asession, card_id: int):
        type_, attr, level, rank, link_rating, p_scale, attack, defense, src_url = (
            "モンスター",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            ""
        )
        monster_types = []
        HEADERS["referer"] = f"https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&request_locale=ja"
        card_url = f"https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=2&cid={card_id}&request_locale=ja"
        r = await self.get_and_render(asession, card_url, HEADERS, self.get_card_info)
        if not r:
            return None
        src_urls = r.html.xpath('//*[@id="card_image_1"]/@src')
        if not src_urls:
            return None
        src_url = src_urls[0]
        info = ["／".join(x.strip() for x in i.split("／")).strip() for i in r.html.xpath('//*[@id="details"]/tbody/tr/td/div//text()') if i.strip()]

        for key, value in zip(info[::2], info[1::2]):
            if key == "効果":
                type_ = value
            if key == "属性":
                attr = value.strip("属性")
            if key == "レベル":
                level = value
            if key == "ランク":
                rank = value
            if key == "リンク":
                link_rating = value
            if key == "ペンデュラムスケール":
                p_scale = value
            if key == "種族" or key == "その他項目":
                monster_types.append(value)
            if key == "攻撃力":
                attack = value
            if key == "守備力":
                defense = value
        return type_, attr, level, rank, link_rating, p_scale, attack, defense, src_url, "／".join(monster_types)

    async def get_card_supplement_info(self, asession, card_id: int):
        card_url = f"{self.prefix}/faq_search.action?ope=4&cid={card_id}&rp=100&request_locale=ja"
        HEADERS["referer"] = f"{self.prefix}/faq_search.action?ope=4&cid={card_id}&request_locale=ja"
        if card_id in self.success_ids['card']:
            return None
        r = await self.get_and_render(asession, card_url, HEADERS, self.get_card_supplement_info)
        if not r:
            self.fail_ids['card'].add(card_id)
            await self.retry(asession)
            return None
        card_info = await self.get_card_info(asession, card_id)
        if card_info is None:
            self.fail_ids['card'].add(card_id)
            return None
        (
            type_, 
            attr,
            level,
            rank,
            link_rating,
            p_scale,
            attack,
            defense,
            src_url,
            types,
        ) = card_info
        card_texts = r.html.xpath('//*[@id="card_text"]/text()')
        if not card_texts:
            self.fail_ids['card'].add(card_id)
            return None
        card_name = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')[0].strip()
        card_text = card_texts[0].strip().replace("「\n", "「").replace("\n」", "」")
        card_supplement = "\n".join(r.html.xpath('//*[@id="supplement"]//text()')).strip().replace("「\n", "「").replace("\n」", "」")
        card_supplement_date = r.html.xpath('//*[@id="card_info"]/div[@id="update_time"]/div/span/text()')[0]
        p_texts = r.html.xpath('//*[@id="pen_effect"]/text()')
        p_effect, p_supplement, p_supplement_date = "", "", ""
        if p_texts:
            p_effect = r.html.xpath('//*[@id="pen_effect"]/text()')[0].strip().replace("「\n", "「").replace("\n」", "」")
            p_supplement = "\n".join(r.html.xpath('//*[@id="pen_supplement"]//text()')).strip().replace("「\n", "「").replace("\n」", "」")
            p_supplement_date = r.html.xpath('//*[@id="pen_info"]/div[@id="update_time"]/div/span/text()')[0]
        try:
            await save_card(
                card_id,
                card_name,
                card_text,
                card_supplement,
                card_supplement_date,
                p_effect,
                p_supplement,
                p_supplement_date,
                type_, 
                attr,
                level,
                rank,
                link_rating,
                p_scale,
                attack,
                defense,
                src_url,
                types,
            )
        except Exception:
            logger.exception(f"card id: {card_id}, card_name: {card_name} save fail: {traceback.format_exc()}")
            self.fail_ids['card'].add(card_id)

        part_urls = r.html.xpath('//div[@class="f_left qa_title"]/input/@value')
        if not part_urls:
            return None
        for part_url in part_urls:
            faq_id = int(part_url.split('&fid=')[1].split('&')[0])
            try:
                await self.get_faq_info(asession, faq_id)
            except Exception:
                logger.exception(f'some error occured: {traceback.format_exc()}')
        pages = r.html.xpath('//div[@class="page_num"]/span/a/text()')
        if pages and pages[-1] == '»':
            await self.get_card_faq_page(self, asession, card_id, 2)

    async def get_card_faq_page(self, asession, card_id: int, page: int):
        card_faq_url = f"{self.prefix}/faq_search.action?ope=4&cid={card_id}&rp=100&sort=2&page={page}&request_locale=ja"
        HEADERS["referer"] = f"{self.prefix}/faq_search.action?ope=4&cid={card_id}&request_locale=ja"
        if (card_id, page) in self.success_ids['card_faq_page']:
            return None
        r = await self.get_and_render(asession, card_faq_url, HEADERS, self.get_card_supplement_info)
        if not r:
            self.fail_ids['card_faq_page'].add((card_id, page))
            await self.retry(asession)
            return None
        part_urls = r.html.xpath('//div[@class="f_left qa_title"]/input/@value')
        if not part_urls:
            self.fail_ids['card_faq_page'].add((card_id, page))
            return None
        for part_url in part_urls:
            faq_id = int(part_url.split('&fid=')[1].split('&')[0])
            try:
                await self.get_faq_info(asession, faq_id)
            except Exception:
                logger.exception(f'some error occured: {traceback.format_exc()}')
        pages = r.html.xpath('//div[@class="page_num"]/span/a/text()')
        if pages and pages[-1] == '»':
            await self.get_card_faq_page(self, asession, card_id, page+1)

    async def get_faq_info(self, asession, faq_id: int):
        if faq_id in self.success_ids['faq']:
            return None
        faq_url = f'{self.prefix}/faq_search.action?ope=5&fid={faq_id}&keyword=&tag=-1&request_locale=ja'
        r = await self.get_and_render(asession, faq_url, HEADERS, self.get_faq_info)
        if not r:
            self.fail_ids['faq'].add(faq_id)
            await self.retry(asession)
            return None
        fetched = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')
        if not fetched:
            self.fail_ids['faq'].add(faq_id)
            return None
        title = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')[0]
        question = "\n".join(r.html.xpath('//*[@id="question_text"]//text()')).strip().replace("「\n", "「").replace("\n」", "」")
        answer = "\n".join(r.html.xpath('//*[@id="answer_text"]//text()')).strip().replace("「\n", "「").replace("\n」", "」")
        tags = r.html.xpath('//*[@id="tag_update"]/div/span[@class="f_left tag_name"]/text()')
        date = r.html.xpath('//*[@id="tag_update"]/div/span[@class="f_right"]/text()')[0]
        card_urls = r.html.xpath('//*[@id="question_text"]/a/@href')
        cards_id = set(int(card_url.split("cid=")[1]) for card_url in card_urls if "cid=" in card_url)

        try:
            await save_faq(cards_id, faq_id, title, question, answer, tags, date)
        except Exception:
            logger.exception(f'faq id: {faq_id}, title: {title}, cards id: {cards_id} save fail: {traceback.format_exc()}')
            self.fail_ids['faq'].add(faq_id)
            return None
