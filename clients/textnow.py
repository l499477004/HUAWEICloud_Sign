import asyncio
import time

from libs.base import BaseClient


class TextNow(BaseClient):

    def __init__(self):
        super().__init__()
        self.url = 'https://www.textnow.com/login'

    async def handler(self, **kwargs):
        self.logger.info(f'{self.username} start login.')
        await self.page.type('#txt-username', self.username, {'delay': 20})
        await asyncio.sleep(1)
        await self.page.type('#txt-password', self.password, {'delay': 20})
        await asyncio.sleep(1)
        await self.page.click('#btn-login')
        await asyncio.sleep(20)

        page_url = self.page.url
        if page_url != 'https://www.textnow.com/messaging':
            title_elements = await self.page.xpath('//div[@class="uikit-text-field__message"]')
            for item in title_elements:
                error_info = await (await item.getProperty('textContent')).jsonValue()
                if error_info:
                    self.logger.error(f'{self.username}: {error_info}')
            await self.send_photo(self.page, 'textnow')
            return

        self.logger.info('login success.')
        await asyncio.sleep(20)

        try:
            await self.page.waitForSelector('.toast-container', {'visible': True})
            await self.page.click('img.js-dismissButton')
        except Exception as e:
            self.logger.warning(e)

        try:
            await self.page.waitForSelector('#newText', {'visible': True})
            await self.page.click('#newText')
        except Exception as e:
            self.logger.warning(e)

        await asyncio.sleep(1)
        sms_content = '{}: {}'.format(self.username, time.strftime('%Y-%m-%d %H:%M:%S'))
        await self.page.type('.newConversationTextField ', '3205001183')
        await asyncio.sleep(1)
        await self.page.click('#text-input')
        await self.page.type('#text-input', sms_content)
        await asyncio.sleep(1)
        await self.page.click('#send_button')
        await asyncio.sleep(2)
        self.logger.info('send msg done.')
