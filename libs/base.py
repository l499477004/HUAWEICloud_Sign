import asyncio
import base64
import hashlib
import hmac
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import pymongo
import requests
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.page import Page


class BaseClient:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.url = None
        self.username = None
        self.parent_user = None
        self.git = None
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
        self.mongo_pwd = '3LCmGDd9gXR3f5d0'

    async def before_run(self):
        pass

    async def after_run(self, **kwargs):
        pass

    async def after_handler(self, **kwargs):
        pass

    async def run(self, **kwargs):
        await self.before_run()

        username_list = kwargs.get('username').split(',')
        password_list = kwargs.get('password').split(',')
        git_list = kwargs.get('git')

        if git_list:
            git_list = git_list.split(',')

        self.logger.warning(username_list)

        for i, username in enumerate(username_list):
            git = git_list[i] if git_list and len(git_list) == len(username_list) else None
            password = password_list[0] if len(password_list) == 1 else password_list[i]
            self.username = username
            self.git = git
            try:
                await self.init(**kwargs)
                result = await self.handler(username=username, password=password, git=git, parent=kwargs.get('parent'),
                                            iam=kwargs.get('iam'))
                await self.after_handler(result=result, username=username)
            except Exception as e:
                self.logger.warning(e)
            finally:
                await self.close()
                await asyncio.sleep(3)

    async def init(self, **kwargs):
        self.browser = await launch(ignorehttpserrrors=True, headless=kwargs.get('headless', True),
                                    args=['--disable-infobars', '--no-sandbox', '--start-maximized'])
        self.page = await self.browser.newPage()
        try:
            self.page.on('dialog', lambda dialog: asyncio.ensure_future(self.close_dialog(dialog)))
        except Exception as e:
            self.logger.warning(e)

        # await self.page.setRequestInterception(True)
        # self.page.on('request', self.intercept_request)

        await self.page.setUserAgent(self.ua)
        await self.page.setViewport({'width': 1200, 'height': 768})

        await self.page.goto(self.url, {'waitUntil': 'load'})

    async def intercept_request(self, request):
        if request.resourceType in ["image"]:
            await request.abort()
        else:
            await request.continue_()

    async def handler(self, **kwargs):
        raise RuntimeError

    async def close(self):
        try:
            await self.page.close()
        except Exception as e:
            self.logger.debug(e)

        try:
            await self.browser.close()
        except Exception as e:
            self.logger.debug(e)

    @staticmethod
    async def close_dialog(dialog):
        await dialog.dismiss()

    @staticmethod
    async def accept_dialog(dialog):
        await dialog.accept()

    @staticmethod
    def send_message(text, title='Notice'):
        ding_url = 'https://oapi.dingtalk.com/robot/send'
        access_token = os.environ.get('DING_TOKEN')
        _timestamp = str(round(time.time() * 1000))
        secret = 'SEC21c976f7bc4cd043739d166df768c692d15aff445062dd321d0f57a97b58b00e'
        secret_enc = secret.encode('utf-8')
        string_to_sign_enc = '{}\n{}'.format(_timestamp, secret).encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code)
        json_data = {'msgtype': 'markdown', 'markdown': {'text': text, 'title': title}}
        params = {'access_token': access_token, 'timestamp': _timestamp, 'sign': sign}
        return requests.post(ding_url, params=params, json=json_data).json()

    @staticmethod
    def get_bj_time():
        utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        return utc_dt.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
