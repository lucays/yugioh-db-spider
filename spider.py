import random
import asyncio
import traceback
from typing import Callable

import pyppeteer

from utils.session import AsyncSession
from configs.log_config import logger
from pipeline import (
    save_or_update_card,
    save_or_update_supplement,
    save_or_update_faq,
    delete_faq,
    card_exist,
    get_faqs_id_date,
)

HEADERS = {
    "referer": "",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.43",
}


class CardDBSpider:
    def __init__(self) -> None:
        self.prefix = "https://www.db.yugioh-card.com/yugiohdb"
        self.fail_ids = {
            "card": set(),
            "supplement": set(),
            "faq": set(),
            "card_page": set(),
            "card_faq_page": set(),
        }
        self.funcs = {
            "card": self.get_card_info,
            "supplement": self.get_card_supplement_info,
            "faq": self.get_faq_info,
            "card_page": self.get_per_page_cards_id,
            "card_faq_page": self.get_card_faq_page,
        }

    async def get_and_render(self, asession, url: str, headers: dict, func: Callable):
        try:
            r = await asession.get(url, headers=headers)
            await r.html.arender(retries=2, sleep=random.randint(1, 5), timeout=60)
            return r
        except pyppeteer.errors.TimeoutError:
            logger.exception(f"request url: {url} fail, func: {func}, error: timeout")
            return None
        except Exception:
            logger.exception(
                f"request url: {url} fail, func: {func}, error: {traceback.format_exc()}"
            )
            return None

    async def retry(self, asession):
        for type_, values in self.fail_ids.items():
            tasks = []
            if type_ == "card_faq_page":
                for value in values:
                    card_id, page = value
                    tasks.append(self.funcs[type_](asession, card_id, page, set()))
            else:
                for value in values:
                    tasks.append(self.funcs[type_](asession, value))
            await self.run_tasks(tasks)

    async def get_cards(self):
        async with AsyncSession() as asession:
            start_page = 1
            await self.get_per_page_cards_id(asession, start_page)

    async def get_per_page_cards_id(self, asession, page: int):
        card_page_url = f"{self.prefix}/card_search.action?ope=1&sess=1&page={page}&mode=2&stype=1&othercon=2&rp=100&request_locale=ja"
        if HEADERS["referer"]:
            HEADERS[
                "referer"
            ] = f"{self.prefix}/card_search.action?ope=1&sess=3&page={page-1}&mode=2&stype=1&othercon=2&rp=100"
        else:
            HEADERS[
                "referer"
            ] = f"{self.prefix}/card_search.action?ope=1&sess=3&page=2&mode=2&stype=1&othercon=2&rp=100"

        r = await self.get_and_render(
            asession, card_page_url, HEADERS, self.get_per_page_cards_id
        )
        if not r:
            self.fail_ids["card_page"].add(page)
            await self.retry(asession)
            return None
        cards_url = r.html.xpath('//*[@id="search_result"]//input/@value')
        if cards_url:
            logger.info(f"start fetch card page: {page} ...")
            tasks = []
            for card_url in cards_url:
                card_id = int(card_url.split("cid=")[1])
                tasks.append(
                    asyncio.create_task(
                        self.get_card_supplement_info(asession, card_id)
                    )
                )
            await self.run_tasks(tasks)
        else:
            self.fail_ids["card_page"].add(page)
            await self.get_per_page_cards_id(asession, page + 1)
        pages = r.html.xpath('//div[@class="page_num"]/span/a/text()')
        if pages and pages[-1] == "»":
            await self.get_per_page_cards_id(asession, page + 1)

    async def run_tasks(self, tasks):
        # 等分task
        count = 2
        sub_task_length = (len(tasks) // count) + 1
        for i in range(count):
            sub_tasks = tasks[i * sub_task_length : (i + 1) * sub_task_length]
            if sub_tasks:
                done, _ = await asyncio.wait(sub_tasks)
                for task in done:
                    try:
                        await task
                    except Exception:
                        logger.exception(
                            f"some error occured: {traceback.format_exc()}"
                        )

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
            "",
        )
        monster_types = []
        HEADERS[
            "referer"
        ] = f"https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&request_locale=ja"
        card_url = f"https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=2&cid={card_id}&request_locale=ja"
        r = await self.get_and_render(asession, card_url, HEADERS, self.get_card_info)
        if not r:
            self.fail_ids["card"].add(card_id)
            return None
        src_urls = r.html.xpath('//*[@id="card_image_1"]/@src')
        if not src_urls:
            return None
        src_url = src_urls[0]
        card_name = [
            i.strip() for i in r.html.xpath('//*[@id="broad_title"]/div/h1/text()')
        ][0]
        info = [
            "／".join(x.strip() for x in i.split("／")).strip()
            for i in r.html.xpath('//*[@id="details"]/tbody/tr/td/div//text()')
            if i.strip()
        ]

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
        await save_or_update_card(
            card_id,
            card_name,
            type_,
            attr,
            level,
            rank,
            link_rating,
            p_scale,
            attack,
            defense,
            src_url,
            "／".join(monster_types),
        )

    async def get_card_supplement_info(self, asession, card_id: int):
        card_url = f"{self.prefix}/faq_search.action?ope=4&cid={card_id}&rp=100&request_locale=ja"
        HEADERS[
            "referer"
        ] = f"{self.prefix}/faq_search.action?ope=4&cid={card_id}&request_locale=ja"

        r = await self.get_and_render(
            asession, card_url, HEADERS, self.get_card_supplement_info
        )
        if not r:
            self.fail_ids["supplement"].add(card_id)
            await self.retry(asession)
            return None

        card_texts = r.html.xpath('//*[@id="card_text"]/text()')
        if not card_texts:
            self.fail_ids["card"].add(card_id)
            return None
        card_name = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')[0].strip()
        card_text = card_texts[0].strip().replace("「\n", "「").replace("\n」", "」")
        card_supplement = (
            "\n".join(r.html.xpath('//*[@id="supplement"]//text()'))
            .strip()
            .replace("「\n", "「")
            .replace("\n」", "」")
        )
        card_supplement_date = r.html.xpath(
            '//*[@id="card_info"]/div[@id="update_time"]/div/span/text()'
        )[0]
        p_texts = r.html.xpath('//*[@id="pen_effect"]/text()')
        p_effect, p_supplement, p_supplement_date = "", "", ""
        if p_texts:
            p_effect = (
                r.html.xpath('//*[@id="pen_effect"]/text()')[0]
                .strip()
                .replace("「\n", "「")
                .replace("\n」", "」")
            )
            p_supplement = (
                "\n".join(r.html.xpath('//*[@id="pen_supplement"]//text()'))
                .strip()
                .replace("「\n", "「")
                .replace("\n」", "」")
            )
            p_supplement_date = r.html.xpath(
                '//*[@id="pen_info"]/div[@id="update_time"]/div/span/text()'
            )[0]

        saved, updated = await save_or_update_supplement(
            card_id,
            card_name,
            card_text,
            card_supplement,
            card_supplement_date,
            p_effect,
            p_supplement,
            p_supplement_date,
        )
        if saved or updated or not await card_exist(card_id):
            await self.get_card_info(asession, card_id)

        part_urls = r.html.xpath('//div[@class="f_left qa_title"]/input/@value')
        dates = [
            i.strip()
            for i in r.html.xpath(
                '//div[@class="list_style"]/ul/li/table/tbody/tr[1]/td/div[2]//text()'
            )
        ]
        if not part_urls:
            return None
        faqs_id_date = await get_faqs_id_date(card_id)
        tasks = []
        for part_url, date in zip(part_urls, dates):
            faq_id = int(part_url.split("&fid=")[1].split("&")[0])
            if (faq_id, date) in faqs_id_date:
                faqs_id_date.remove((faq_id, date))
                continue
            tasks.append(asyncio.create_task(self.get_faq_info(asession, faq_id)))
        await self.run_tasks(tasks)
        pages = r.html.xpath('//div[@class="page_num"]/span/a/text()')
        if pages and pages[-1] == "»":
            await self.get_card_faq_page(asession, card_id, 2, faqs_id_date)

    async def get_card_faq_page(self, asession, card_id: int, page: int, faqs_id_date):
        card_faq_url = f"{self.prefix}/faq_search.action?ope=4&cid={card_id}&rp=100&sort=2&page={page}&request_locale=ja"
        HEADERS[
            "referer"
        ] = f"{self.prefix}/faq_search.action?ope=4&cid={card_id}&request_locale=ja"

        r = await self.get_and_render(
            asession, card_faq_url, HEADERS, self.get_card_faq_page
        )
        if not r:
            self.fail_ids["card_faq_page"].add((card_id, page))
            await self.retry(asession)
            return None
        part_urls = r.html.xpath('//div[@class="f_left qa_title"]/input/@value')
        dates = [
            i.strip()
            for i in r.html.xpath(
                '//div[@class="list_style"]/ul/li/table/tbody/tr[1]/td/div[2]//text()'
            )
        ]
        if not part_urls:
            self.fail_ids["card_faq_page"].add((card_id, page))
            return None
        tasks = []
        for part_url, date in zip(part_urls, dates):
            faq_id = int(part_url.split("&fid=")[1].split("&")[0])
            if (faq_id, date) in faqs_id_date:
                faqs_id_date.remove((faq_id, date))
                continue
            tasks.append(asyncio.create_task(self.get_faq_info(asession, faq_id)))
        await self.run_tasks(tasks)
        pages = r.html.xpath('//div[@class="page_num"]/span/a/text()')
        if pages and pages[-1] == "»":
            await self.get_card_faq_page(asession, card_id, page + 1, faqs_id_date)
        elif faqs_id_date:
            for faq_id, date in faqs_id_date:
                delete_faq(faq_id)

    async def get_faq_info(self, asession, faq_id: int):
        faq_url = f"{self.prefix}/faq_search.action?ope=5&fid={faq_id}&keyword=&tag=-1&request_locale=ja"
        r = await self.get_and_render(asession, faq_url, HEADERS, self.get_faq_info)
        if not r:
            self.fail_ids["faq"].add(faq_id)
            await self.retry(asession)
            return None
        fetched = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')
        if not fetched:
            self.fail_ids["faq"].add(faq_id)
            return None
        title = r.html.xpath('//*[@id="broad_title"]/div/h1/text()')[0]
        question = (
            "\n".join(r.html.xpath('//*[@id="question_text"]//text()'))
            .strip()
            .replace("「\n", "「")
            .replace("\n」", "」")
        )
        answer = (
            "\n".join(r.html.xpath('//*[@id="answer_text"]//text()'))
            .strip()
            .replace("「\n", "「")
            .replace("\n」", "」")
        )
        tags = r.html.xpath(
            '//*[@id="tag_update"]/div/span[@class="f_left tag_name"]/text()'
        )
        date = r.html.xpath('//*[@id="tag_update"]/div/span[@class="f_right"]/text()')[
            0
        ]
        card_urls = r.html.xpath('//*[@id="question_text"]/a/@href')
        cards_id = set(
            int(card_url.split("cid=")[1])
            for card_url in card_urls
            if "cid=" in card_url
        )

        try:
            await save_or_update_faq(
                cards_id, faq_id, title, question, answer, tags, date
            )
        except Exception:
            logger.exception(
                f"faq id: {faq_id}, title: {title}, cards id: {cards_id} save fail: {traceback.format_exc()}"
            )
