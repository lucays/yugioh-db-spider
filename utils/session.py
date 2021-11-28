from requests_html import AsyncHTMLSession
from configs.config import PROXIES


class AsyncSession:
    def __init__(self):
        self.asession = AsyncHTMLSession(browser_args=['--no-sandbox', f'--proxy-server={PROXIES}'])

    async def __aenter__(self):
        return self.asession

    async def __aexit__(self, exc_type, exc, traceback):
        await self.asession.close()
