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

        await self.sign_task()

        utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        h = int(utc_dt.astimezone(timezone(timedelta(hours=8))).strftime('%H'))
        await self.start()
        await self.print_credit(self.username)


    async def login(self, username, password):
        await self.page.waitForSelector('input[name="userAccount"]')
        await asyncio.sleep(1)
        await self.page.type('input[name="userAccount"]', username, {'delay': 10})
        await asyncio.sleep(3)
        await self.page.type('.hwid-input-pwd', password, {'delay': 10})
        await asyncio.sleep(5)
        await self.page.click('.hwid-list-row-active')
        await self.page.type('.hwid-input-pwd', password, {'delay': 10})
        await asyncio.sleep(2)
        await self.page.click('.normalBtn')
        await asyncio.sleep(5)
        self.logger.info(f'跳过升级')
        await self.page.goto('https://devcloud.huaweicloud.com/bonususer/home/makebonus', {'waitUntil': 'load'})
        await asyncio.sleep(5)


    async def iam_login(self, username, password, parent):
        self.parent_user = os.environ.get('PARENT_USER', parent)

        for i in range(4):
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
                break
            except Exception as e:
                self.logger.debug(e)
                await self.page.goto(self.url, {'waitUntil': 'load'})

    async def get_cookies(self):
        cookies = await self.page.cookies()
        new_cookies = {}
        for cookie in cookies:
            new_cookies[cookie['name']] = cookie['value']
        return new_cookies
