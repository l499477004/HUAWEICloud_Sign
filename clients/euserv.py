import asyncio

from libs.base import BaseClient


class Euserv(BaseClient):

    def __init__(self):
        super().__init__()
        self.url = 'https://support.euserv.com'

    async def handler(self, **kwargs):
        self.logger.info(f'{self.username} start login.')
        await self.page.type('input[name="email"]', self.username, {'delay': 30})
        await asyncio.sleep(0.5)
        await self.page.type('input[name="password"]', self.password, {'delay': 30})
        await asyncio.sleep(0.5)
        await self.page.click('input[name="Submit"]')
        await asyncio.sleep(10)

        self.logger.info(self.page.url)
        await self.page.click('#kc2_order_customer_orders_tab_1')

        await asyncio.sleep(1)

        s = await self.page.Jeval('.kc2_order_extend_contract_term_container', 'el => el.textContent')
        self.logger.info(s)
        if type(s) == str and s.find('Contract extension possible from') != -1:
            return

        try:
            await self.page.click('.kc2_order_extend_contract_term_container')
            await asyncio.sleep(15)
            await self.page.click('.kc2_customer_contract_details_change_plan_item_action_button')
            await asyncio.sleep(5)
            await self.page.type('input[name="password"]', self.password, {'delay': 30})
            await asyncio.sleep(1)
            await self.page.click('#kc2_security_password_dialog_action_confirm')
            await asyncio.sleep(5)
            await self.page.click('input[value="Confirm"]')
            await asyncio.sleep(5)
        except Exception as e:
            self.logger.error(e)
            await self.send_photo(self.page, 'euserv')
