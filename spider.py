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
        self.fail_urls = set()
        self.success_urls = set()
        self.faq_urls = set()
        self.MAX_CARD_PAGE = 115

    async def get_and_render(self, asession, url: str, headers: dict, func: Callable):
        try:
            r = await asession.get(url, headers=headers)
            await r.html.arender(retries=3, sleep=random.uniform(0.3, 0.6), timeout=20)
            self.success_urls.add(url)
            return r
        except:
            self.fail_urls.add((url, func))
            logger.error(f'request url: {url} fail, func: {func}')
            return None

    async def retry(self, asession):
        while self.fail_urls:
            url, func = self.fail_urls.pop()
            await func(asession, url)

    async def get_cards(self):
        async with AsyncSession() as asession:
            start_page = 1
            start_card_page_url = f"{self.prefix}/card_search.action?ope=1&sess=1&page={start_page}&mode=2&stype=1&othercon=2&rp=100&request_locale=ja"
            await self.get_per_page_cards_id(asession, start_card_page_url)

    async def get_per_page_cards_id(self, asession, card_page_url: str):
        page = int(card_page_url.split("&page=")[1].split("&")[0])
        if HEADERS["referer"]:
            HEADERS["referer"] = f"{self.prefix}/card_search.action?ope=1&sess=3&page={page-1}&mode=2&stype=1&othercon=2&rp=100"
        else:
            HEADERS["referer"] = f"{self.prefix}/card_search.action?ope=1&sess=3&page=2&mode=2&stype=1&othercon=2&rp=100"
        if card_page_url in self.success_urls:
            return None
        r = await self.get_and_render(asession, card_page_url, HEADERS, self.get_per_page_cards_id)
        if not r:
            await self.retry(asession)
            return None
        cards_url = r.html.xpath('//*[@id="search_result"]//input/@value')
        if cards_url:
            for card_url in cards_url:
                card_id = card_url.split("cid=")[1]
                card_url = f"https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&sort=2&page=1&request_locale=ja"
                try:
                    await self.get_card_supplement_info(asession, card_url)
                except Exception:
                    logger.info(f'some error occured: {traceback.format_exc()}')
        else:
            self.fail_urls.add((card_page_url, self.get_per_page_cards_id))
            next_page_url = f"{self.prefix}/card_search.action?ope=1&sess=1&page={page+1}&mode=2&stype=1&othercon=2&rp=100&request_locale=ja"
            await self.get_per_page_cards_id(asession, next_page_url)
        pages = r.html.xpath('//div[@class="page_num"]/span/a/text()')
        if pages and pages[-1] == '»':
            next_page_url = f"{self.prefix}/card_search.action?ope=1&sess=1&page={page+1}&mode=2&stype=1&othercon=2&rp=100&request_locale=ja"
            await self.get_per_page_cards_id(asession, next_page_url)

    async def get_card_info(self, asession, card_id: str):
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
        if card_url in self.success_urls:
            return None
        r = await self.get_and_render(asession, card_url, HEADERS, self.get_card_info)
        if not r:
            return attr, level, rank, link_rating, p_scale, attack, defense, src_url, "／".join(monster_types)
        src_url = r.html.xpath('//*[@id="card_image_1"]/@src')[0]
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

    async def get_card_supplement_info(self, asession, card_url: str):
        page = int(card_url.split("&page=")[1].split("&")[0])
        card_id = int(card_url.split("cid=")[1].split("&")[0])
        HEADERS["referer"] = f"https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&request_locale=ja"
        if card_url in self.success_urls:
            return None
        r = await self.get_and_render(asession, card_url, HEADERS, self.get_card_supplement_info)
        if not r:
            await self.retry(asession)
            return None
        if page == 1:
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
            ) = await self.get_card_info(asession, card_id)
            card_name = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')[0].strip()
            card_text = r.html.xpath('//*[@id="card_text"]/text()')[0].strip().replace("「\n", "「").replace("\n」", "」")
            card_supplement = "\n".join(r.html.xpath('//*[@id="supplement"]//text()')).strip().replace("「\n", "「").replace("\n」", "」")
            card_supplement_date = r.html.xpath('//*[@id="card_info"]/div[@id="update_time"]/div/span/text()')[0]
            p_texts = r.html.xpath('//*[@id="pen_effect"]/text()')
            p_effect, p_supplement, p_supplement_date = "", "", ""
            if p_texts:
                p_effect = r.html.xpath('//*[@id="pen_effect"]/text()')[0].strip().replace("「\n", "「").replace("\n」", "」")
                p_supplement = "\n".join(r.html.xpath('//*[@id="pen_supplement"]//text()')).strip().replace("「\n", "「").replace("\n」", "」")
                p_supplement_date = r.html.xpath('//*[@id="pen_info"]/div[@id="update_time"]/div/span/text()')[0]

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
            logger.info(f"card id: {card_id}, card_name: {card_name} saved")

        part_urls = r.html.xpath('//div[@class="f_left qa_title"]/input/@value')
        if not part_urls:
            return None
        for part_url in part_urls:
            faq_url = f"https://www.db.yugioh-card.com/{part_url}&request_locale=ja"
            if faq_url in self.faq_urls:
                continue
            try:
                await self.get_faq_info(asession, faq_url)
            except Exception:
                logger.info(f'some error occured: {traceback.format_exc()}')
        pages = r.html.xpath('//div[@class="page_num"]/span/a/text()')
        if pages and pages[-1] == '»':
            next_page_url = f"https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&sort=2&page={page+1}&request_locale=ja"
            await self.get_card_supplement_info(asession, next_page_url)

    async def get_faq_info(self, asession, faq_url: str):
        faq_id = int(faq_url.split("fid=")[1].split("&")[0])
        if faq_url in self.success_urls:
            return None
        r = await self.get_and_render(asession, faq_url, HEADERS, self.get_faq_info)
        if not r:
            await self.retry(asession)
            return None
        self.faq_urls.add(faq_url)
        fetched = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')
        if not fetched:
            self.fail_urls.add((faq_url, self.get_faq_info))
            return None
        title = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')[0]
        question = "\n".join(r.html.xpath('//*[@id="question_text"]//text()')).strip().replace("「\n", "「").replace("\n」", "」")
        answer = "\n".join(r.html.xpath('//*[@id="answer_text"]//text()')).strip().replace("「\n", "「").replace("\n」", "」")
        tags = r.html.xpath('//*[@id="tag_update"]/div/span[@class="f_left tag_name"]/text()')
        date = r.html.xpath('//*[@id="tag_update"]/div/span[@class="f_right"]/text()')[0]
        card_urls = r.html.xpath('//*[@id="question_text"]/a/@href')
        cards_id = set(int(card_url.split("cid=")[1]) for card_url in card_urls if "cid=" in card_url)

        await save_faq(cards_id, faq_id, title, question, answer, tags, date)
        logger.info(f"faq id: {faq_id}, title: {title}, cards id: {cards_id} saved")
