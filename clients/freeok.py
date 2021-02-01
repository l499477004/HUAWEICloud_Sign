import asyncio
import time

from libs.base import BaseClient


class FreeOk(BaseClient):

    def __init__(self):
        super().__init__()
        self.url = 'https://v2.freeok.xyz/auth/login'

    async def handler(self, username, password, **kwargs):
        self.logger.info(f'{username} start login.')
        await self.page.type('#email', username, {'delay': 30})
        await asyncio.sleep(0.5)
        await self.page.type('#passwd', password, {'delay': 30})
        await asyncio.sleep(0.5)
        await self.page.click('.checkbox-adv')
        await asyncio.sleep(0.5)
        await self.page.click('#login')
        await asyncio.sleep(5)

        page_url = self.page.url
        if page_url == 'https://v2.freeok.xyz/user/disable':
            await self.page.type('#email', username)
            await self.page.click('#reactive')
            self.logger.info('reactive success.')
            await asyncio.sleep(10)
        else:
            await self.page.click('#checkin')
            await asyncio.sleep(2)
