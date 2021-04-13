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
        await self.page.waitForSelector('.hwid-input.hwid-cover-input.userAccount')
        if kwargs.get('iam'):
            await self.iam_login(self.username, self.password, kwargs.get('parent'))
        else:
            await self.login(self.username, self.password)

        url = self.page.url
        if 'login' in url:
            self.logger.error(f'{self.username} login fail.')
            return None

        if 'bonususer/home/makebonus' not in url:
            await self.page.goto('https://devcloud.huaweicloud.com/bonususer/home/makebonus', {'waitUntil': 'load'})

        await self.sign_task()

        utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        h = int(utc_dt.astimezone(timezone(timedelta(hours=8))).strftime('%H'))
        self.logger.info(f'now hours: {h}')
        await self.sign_task()

        if h <= 13:
            await self.check_project()
            await self.start()
            await self.add_address()

        if h > 13:
            await self.delete_project()
            await self.delete_function()
            await self.delete_api()
            await self.delete_api_group()

        # 3月23日-4月20日
        await self.hdc_floor()
        # 钉钉发送消息
        if h > 21:
            await self.print_credit(self.username)

        return await self.get_credit()

    async def login(self, username, password):
        await asyncio.sleep(5)
        await self.page.type('.hwid-input.hwid-cover-input.userAccount', username)
        await asyncio.sleep(0.5)
        await self.page.type('.hwid-input-pwd', password)
        await self.page.click('.normalBtn')
        await asyncio.sleep(5)
        items = await self.page.querySelectorAll('.mutilAccountList .hwid-list-radio')
        if len(items):
            await items[1].click()
            await asyncio.sleep(0.5)
            await self.page.click('.hwid-mutilAccountMenu .normalBtn')
            await asyncio.sleep(5)

    async def iam_login(self, username, password, parent):
        await self.page.type('#IAMUsernameInputId', username)
        await asyncio.sleep(0.5)
        await self.page.type('#IAMPasswordInputId', password)
        await self.page.click('#loginBtn')
        await asyncio.sleep(5)

    async def get_cookies(self):
        cookies = await self.page.cookies()
        new_cookies = {}
        for cookie in cookies:
            new_cookies[cookie['name']] = cookie['value']
        return new_cookies
