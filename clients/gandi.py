import argparse
import asyncio
import logging
import random
import string
import time

from pyppeteer import launch


async def main(username, password):
    browser = await launch(ignorehttpserrrors=True, headless=True,
                           args=['--disable-infobars', '--no-sandbox', '--window-size=1920,1080'])

    for i in range(20):
        print(time.strftime('%Y-%m-%d %H:%M:%S'))
        page = await browser.newPage()

        try:
            email_suffix = ['demo666.cn', 'zzcworld.com', 'mail01.eu.org']
            name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            email = f'{name}@{random.choice(email_suffix)}'

            # await page.setViewport({'width': 1920, 'height': 1080})
            await page.goto('https://20.gandi.net/zh-hant/lottery-wheel/', {'waitUntil': 'load'})

            await page.waitForSelector('#email', {'visible': True})

            await page.type('#email', email)
            await asyncio.sleep(1)

            await page.evaluate(
                '''() =>{ document.getElementById('reglement').checked=true }''')

            await page.evaluate(
                '''() =>{ document.getElementById('newsLetter').checked=true }''')

            await asyncio.sleep(1)

            await page.click('#gandi20Years-wheel-form-submit')

            await asyncio.sleep(5)
            await page.close()
        except Exception as e:
            print(e)
            await page.close()
        await asyncio.sleep(10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--username')
    parser.add_argument('--password')
    args = parser.parse_args()
    params = vars(args)

    asyncio.get_event_loop().run_until_complete(main(params.get('username'), params.get('password')))
