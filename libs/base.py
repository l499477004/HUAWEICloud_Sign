import asyncio
import base64
import hashlib
import hmac
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests
from pyppeteer import launch, launcher
from pyppeteer.browser import Browser
from pyppeteer.network_manager import Request
from pyppeteer.page import Page

import urllib.parse
import json


class BaseClient:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.url = None
        self.username = None
        self.password = None
        self.parent_user = None
        self.git = None
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        self.width = 1440
        self.height = 900
    
    @staticmethod
    def dingding_bot(content, title='HW'):
        timestamp = str(round(time.time() * 1000))  # 时间戳
        access_token = os.environ.get('DING_TOKEN')
        secret = os.environ.get('DING_SECRET')
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))  # 签名
        print('开始使用 钉钉机器人 推送消息...', end='')
        url = f'https://oapi.dingtalk.com/robot/send?access_token={access_token}&timestamp={timestamp}&sign={sign}'
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        data = {
            'msgtype': 'text',
            'text': {'content': f'{title}\n\n{content}'}
        }
        response = requests.post(url=url, data=json.dumps(data), headers=headers, timeout=15).json()
        if not response['errcode']:
            print('推送成功！')
        else:
            print('推送失败！')

    @staticmethod
    def pushPlusSend(content, title):
        token = os.environ.get('PUSHPLUS_TOKEN')
        url = 'http://www.pushplus.plus/send'
        print('开始使用 PUSHPLUS 推送消息...', end='')
        data = {
            "token":token,
            "title":title,
            "content":content,
            'template': 'json'
        }
        body=json.dumps(data).encode(encoding='utf-8')
        headers = {'Content-Type':'application/json'}
        response = requests.post(url,data=body,headers=headers)
        if not response['errcode']:
            print('推送成功！')
        else:
            print('推送失败！')

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

        self.logger.warning(username_list)

        for i, username in enumerate(username_list):
            password = password_list[0] if len(password_list) == 1 else password_list[i]
            self.username = username
            self.password = password
            try:
                await self.init(**kwargs)
                await self.handler(**kwargs)
            except Exception as e:
                self.logger.exception(e)
            finally:
                await self.close()
                await asyncio.sleep(3)

    async def init(self, **kwargs):
        # launcher.DEFAULT_ARGS.remove('--enable-automation')
        self.browser = await launch(ignorehttpserrrors=True, headless=kwargs.get('headless', True),
                                    args=['--disable-infobars', '--disable-web-security', '--no-sandbox',
                                          '--start-maximized', '--disable-features=IsolateOrigins,site-per-process'])
        self.page = await self.browser.newPage()
        try:
            self.page.on('dialog', lambda dialog: asyncio.ensure_future(self.close_dialog(dialog)))
        except Exception as e:
            self.logger.warning(e)

        await self.page.setUserAgent(self.ua)
        await self.page.setViewport(viewport={'width': self.width, 'height': self.height})

        js_text = """
        () =>{
            Object.defineProperties(navigator,{ webdriver:{ get: () => false } });
            window.navigator.chrome = { runtime: {},  };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5,6], });
         }
            """
        await self.page.evaluateOnNewDocument(js_text)

        # await self.page.setRequestInterception(True)
        # self.page.on('request', self.intercept_request)

        await self.page.goto(self.url, {'waitUntil': 'load'})

    async def intercept_request(self, request: Request):
        self.logger.info(request.url)
        if request.resourceType in ["image"]:
            await request.abort()
        else:
            await request.continue_()

    async def get_cookies(self):
        cookies = await self.page.cookies()
        new_cookies = {}
        for cookie in cookies:
            new_cookies[cookie['name']] = cookie['value']
        return new_cookies

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
            # os.system("kill -9 `ps -ef|grep chrome|grep -v grep|awk '{print $2}'`")
            self.browser = None

    @staticmethod
    async def close_dialog(dialog):
        await dialog.dismiss()

    @staticmethod
    async def accept_dialog(dialog):
        await dialog.accept()

    @staticmethod
    def get_bj_time():
        utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        return utc_dt.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')

