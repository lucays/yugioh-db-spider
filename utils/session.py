import pyppeteer

from requests_html import AsyncHTMLSession


class AsyncHTMLSession2(AsyncHTMLSession):

    @property
    async def browser(self):
        if not hasattr(self, "_browser"):
            return await pyppeteer.launch(headless=True, args=['--no-sandbox', '--proxy-server=<your proxy or delete this arg>'])


class AsyncSession:
    def __init__(self):
        self.asession = AsyncHTMLSession2()

    async def __aenter__(self):
        return self.asession

    async def __aexit__(self, exc_type, exc, traceback):
        await self.asession.close()
