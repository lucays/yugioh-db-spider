
import random
import asyncio

from requests_html import AsyncHTMLSession

headers = {
    'cookie': 'Edgescape=3; Analytics=2; CountryCd=CN; yugiohdb_cookie_card_search_mode=2; JSESSIONID=1E0FDEEE72F0A32A457DFF97E0FAB8D5; visid_incap_1363207=nmtsXj6IQrifJgapUwts3bPbs18AAAAAQUIPAAAAAABJgc4/HQrpxjHo0+CEyWID; _ga=GA1.2.1856693357.1605622812; AG=2; _gid=GA1.2.432604883.1624356860; nlbi_1363207=1wS5O8rbSysR5JNsxbLhpQAAAACYu+akurQqZKdvoX91jf2N; incap_ses_637_1363207=LGFKeWcJEE+HsFmGcRTXCFzL0WAAAAAAqIBoyek9KilLDqACbLRtCw==; incap_ses_958_1363207=De6VVui7RBBswoZ4R4BLDZjZ0WAAAAAAn9WOKhn7F5lJWWreIWCqxw==; incap_ses_1203_1363207=AlaxVui1pxQzp9MtdOqxELHe0WAAAAAAvpnxflQRPIogodurvbYG0A==; AWSALB=kUyiK7D/l31lzVjmZOb+GAmvlwO8ZmM7TS2XPbpoMLs73pLWfIbTbyQvGP/6vEfG8qzb46GaeqHzEtmAVIpPh6EgSmDw1FtOIrUXOxJCGXjSl8qYchXDOQ4awVi/; AWSALBCORS=kUyiK7D/l31lzVjmZOb+GAmvlwO8ZmM7TS2XPbpoMLs73pLWfIbTbyQvGP/6vEfG8qzb46GaeqHzEtmAVIpPh6EgSmDw1FtOIrUXOxJCGXjSl8qYchXDOQ4awVi/',
    'referer': 'https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&sess=3&page=2&mode=2&stype=1&othercon=2&rp=100',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.54'
}

visited_urls = set()
# asession = AsyncHTMLSession()


class MyAsyncHTMLSession:
    def __init__(self):
        self.asession = AsyncHTMLSession()

    async def __aenter__(self):
        return self.asession

    async def __aexit__(self, exc_type, exc, traceback):
        await self.asession.close()


async def get_per_page_cards_id(asession: AsyncHTMLSession, page: int, cards_id: list):
    """获取每一页的card id list

    Args:
        asession (AsyncHTMLSession): AsyncHTMLSession
        page (int): 页数
        cards_id (list): card id list
    """
    card_page_url = f'https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&sess=1&page={page}&mode=2&stype=1&othercon=2&rp=100&request_locale=ja'
    r = await asession.get(card_page_url, headers=headers)
    await r.html.arender(sleep=random.randrange(1, 2))
    count = r.html.xpath('//*[@id="article_body"]/table/tbody/tr/td/div[1]/div/strong//text()')[0]
    print(count)
    cards_url = r.html.xpath('//*[@id="search_result"]//input/@value')
    current_page_cards_id = [i.split('cid=')[1] for i in cards_url]
    if current_page_cards_id:
        cards_id.extend(current_page_cards_id)
        await get_per_page_cards_id(asession, page+1)
    print(page, cards_id)

async def get_cards_id():
    async with MyAsyncHTMLSession() as asession:
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
    headers['referer'] = f'https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&request_locale=ja'
    r = await asession.get(card_info_url, headers=headers)
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
    async with MyAsyncHTMLSession() as asession:
        for card_id in cards_id:
            card_info_url = f'https://www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid={card_id}&request_locale=ja'
            

asyncio.run(get_cards_id())
