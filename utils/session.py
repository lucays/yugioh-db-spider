import requests
from requests_html import AsyncHTMLSession

from configs.config import PROXIES


class AsyncSession:
    def __init__(self):
        browser_args = ["--no-sandbox"]
        if PROXIES:
            browser_args = ["--no-sandbox", f"--proxy-server={PROXIES}"]
        self.asession = AsyncHTMLSession(browser_args=browser_args)
        adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
        self.asession.mount("https://", adapter)

    async def __aenter__(self):
        return self.asession

    async def __aexit__(self, exc_type, exc, traceback):
        await self.asession.close()
