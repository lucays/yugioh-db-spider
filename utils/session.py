
from requests_html import AsyncHTMLSession


class AsyncSession:
    def __init__(self):
        self.asession = AsyncHTMLSession()

    async def __aenter__(self):
        return self.asession

    async def __aexit__(self, exc_type, exc, traceback):
        await self.asession.close()
