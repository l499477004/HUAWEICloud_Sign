import asyncio
import os
from datetime import datetime, timezone, timedelta

from libs.base_huawei import BaseHuaWei


class HuaWei(BaseHuaWei):

    def __init__(self):
        super().__init__()

    async def handler(self, **kwargs):
        self.cancel = False

        self.logger.info(f'{self.username} start login.')
        if kwargs.get('iam'):
            await self.iam_login(self.username, self.password, kwargs.get('parent'))
        else:
            await self.login(self.username, self.password)

        url = self.page.url
        if 'login' in url:
            self.logger.error(f'{self.username} login fail.')
            return None

        # 口令盖楼
        await self.hdc_floor()

        return await self.get_credit()

    async def login(self, username, password):
        await self.page.waitForSelector('input[name="userAccount"]')
        await asyncio.sleep(1)
        await self.page.type('input[name="userAccount"]', username, {'delay': 10})
        await asyncio.sleep(0.5)
        await self.page.type('.hwid-input-pwd', password, {'delay': 10})
        await asyncio.sleep(2)
        items = await self.page.querySelectorAll('.hwid-list-row-active')

        if items and len(items):
            await items[0].click()
            await asyncio.sleep(1)

        await self.page.click('.normalBtn')
        await asyncio.sleep(5)

    async def iam_login(self, username, password, parent):
        self.parent_user = os.environ.get('PARENT_USER', parent)

        try:
            await self.page.waitForSelector('#IAMLinkDiv')
            await asyncio.sleep(5)
            await self.page.click('#IAMLinkDiv')
            await asyncio.sleep(1)
            await self.page.type('#IAMAccountInputId', self.parent_user, {'delay': 10})
            await asyncio.sleep(0.5)
            await self.page.type('#IAMUsernameInputId', username, {'delay': 10})
            await asyncio.sleep(0.5)
            await self.page.type('#IAMPasswordInputId', password, {'delay': 10})
            await self.page.click('#loginBtn')
            await asyncio.sleep(5)
        except Exception as e:
            self.logger.exception(e)

    async def get_cookies(self):
        cookies = await self.page.cookies()
        new_cookies = {}
        for cookie in cookies:
            new_cookies[cookie['name']] = cookie['value']
        return new_cookies
