import asyncio
import os
import random
import string
import time

import requests

from libs.base import BaseClient

name_map = {
    '项目管理': [['week_new_project', 0]],
    '代码托管': [['week_new_git', 0], ['open_code_task', 1], ['push_code_task', 2]],
    'CloudIDE': [['open_ide_task', 0]],
    '代码检查': [['week_new_code_check', 0], ['check_code_task', 1]],
    '编译构建': [['week_new_compile_build', 0], ['compile_build_task', 1]],
    '部署': [['deploy_task', 1]],
    '发布': [['upload_task', 0]],
    '流水线': [['week_new_pipeline', 0], ['pipeline_task', 1]],
    '接口测试': [['week_new_api_test_task', 0], ['api_test_task', 1]],
    '测试管理': [['new_test_task', 0]],
    'APIG网关': [['new_new_api_task', 0], ['run_api_task', 1]],
    '函数工作流': [['new_fun_task', 0]],
    '使用API  Explorer完在线调试': 'api_explorer_task',
    '使用API Explorer在线调试': 'api2_explorer_task',
    '使用Devstar生成代码工程': 'dev_star_task',
    '浏览Codelabs代码示例': 'view_code_task',
    '体验DevStar快速生成代码': 'fast_dev_star',
}

init_name_map = {
    # '项目管理': [['week_new_project', 0]],
    # '代码托管': [['week_new_git', 0]],
    # '代码检查': [['week_new_code_check', 0]],
    # '编译构建': [['week_new_compile_build', 0]],
    # '部署': [['week_new_deploy', 0]],
    # '流水线': [['week_new_pipeline', 0]],
    '使用API  Explorer完在线调试': 'api_explorer_task',
    '使用API Explorer在线调试': 'api_explorer_task',
    # '使用Devstar生成代码工程': 'dev_star_task',
}


class BaseHuaWei(BaseClient):

    def __init__(self):
        super().__init__()
        self.url = 'https://devcloud.huaweicloud.com/bonususer/home/makebonus'
        self.task_page = None
        self.create_done = True
        self.home_url = None
        self.cancel = False

    async def after_handler(self, **kwargs):
        credit = kwargs.get('result')
        username = kwargs.get('username')
        if credit:
            self.logger.warning(f"{username} -> {credit}\n")
            if type(credit) == str:
                credit = int(credit.replace('码豆', '').strip())

            _id = f'{self.parent_user}_{username}' if self.parent_user else self.username
            requests.post(f'{self.api}/huawei/save', {'name': _id, 'credit': credit})

    async def start(self):
        if self.page.url != self.url:
            await self.page.goto(self.url, {'waitUntil': 'load'})

        id_list = ['experience-missions', 'middleware-missions']
        for _id in id_list:
            try:
                await self.execute(_id, 'ul.devui-nav li.ng-star-inserted', '', True, name_map)
            except Exception as e:
                self.logger.debug(e)

        try:
            await self.regular()
        except Exception as e:
            self.logger.debug(e)

        try:
            await self.init_account()
        except Exception as e:
            self.logger.debug(e)

    async def regular(self):
        await self.execute('regular-missions', '.daily-list li', 'feedback-', False, name_map)

    async def init_account(self):
        # await self.execute('experience-missions', 'ul.devui-nav li.ng-star-inserted', '', True, init_name_map)

        await self.page.goto('https://devcloud.huaweicloud.com/bonususer/home/new', {'waitUntil': 'load'})
        await asyncio.sleep(2)
        await self.execute('new-tasks-box', 'li.hot-task-item', 'new-task', False, init_name_map)

    async def execute(self, element_id, element_list_name, task_node, is_tab=True, task_map=None):
        elements = await self.page.querySelectorAll(f'#{element_id} {element_list_name}')
        for i, element in enumerate(elements):
            if self.cancel:
                break

            if is_tab:
                name = str(await element.Jeval('a', 'el => el.textContent')).strip()
                task_list = task_map.get(name)
                if task_list is None:
                    continue

                for task in task_list:
                    await element.click()
                    await asyncio.sleep(1)
                    task_node = f'#{element_id} #{element_id}-{task[1]}'
                    await self.run_task(task_node, task[0])
            else:
                _task_node = f'#{element_id} #{task_node}{i}'
                task_name = str(await self.page.Jeval(f'{_task_node} h5', 'el => el.textContent')).strip()
                if not task_map.get(task_name):
                    continue

                await self.run_task(_task_node, task_map.get(task_name))

    async def is_done(self, node, task_fun):
        try:
            is_done = await self.page.querySelector(f"{node} .complate-img")
            if is_done:
                if self.create_done and 'week' in task_fun:
                    return False
                return True
            is_done = await self.page.querySelector(f"{node} img.completed")
            if is_done:
                if self.create_done and 'week' in task_fun:
                    return False
                return True
        except Exception as e:
            self.logger.debug(e)
        return False

    async def run_task(self, task_node, task_fun):
        task_name = await self.page.Jeval(f'{task_node} h5', 'el => el.textContent')

        if await self.is_done(task_node, task_fun):
            self.logger.warning(f'{task_name} -> DONE.')
            return True

        await self.page.click(task_node)
        await asyncio.sleep(2)
        self.logger.info(f'{task_name}')

        try:
            self.task_page = await self.get_new_page()
            await self.task_page.setUserAgent(self.ua)
        except Exception as e:
            self.logger.error(e)
            raise e

        try:
            func = getattr(self, task_fun)
            # await func()
            await asyncio.wait_for(func(), timeout=100.0)
            self.logger.warning(f'{task_name} -> DONE.')
        except asyncio.TimeoutError as t:
            self.logger.debug(t)
            # await self.send_photo(self.task_page, task_fun)
        except Exception as e:
            self.logger.error(e)
        finally:
            await self.close_page()
            await asyncio.sleep(2)
            return True

    async def get_credit(self):
        for i in range(3):
            if self.page.url != self.url:
                await self.page.goto(self.url, {'waitUntil': 'load'})
            else:
                await self.page.reload({'waitUntil': 'load'})
            await asyncio.sleep(5)
            try:
                return str(await self.page.Jeval('#homeheader-coins', 'el => el.textContent')).replace('码豆', '').strip()
            except Exception as e:
                self.logger.debug(e)
        return 0

    async def print_credit(self, user_name):
        new_credit = await self.get_credit()
        self.logger.info(f'码豆: {new_credit}')
        message = f'{user_name} -> {new_credit}'
        self.dingding_bot(message, '华为云码豆')

    async def sign_task(self):
        try:
            await asyncio.sleep(5)
            info = await self.page.Jeval(
                '#homeheader-signin span.button-content, #homeheader-signined  span.button-content',
                'el => el.textContent')
            sign_txt = str(info).strip()
            self.logger.info(sign_txt)
            if sign_txt.find('已签到') == -1:
                await self.page.click('#homeheader-signin')
                await asyncio.sleep(3)
        except Exception as e:
            self.logger.warning(e)

    async def get_new_page(self):
        await asyncio.sleep(2)
        await self.page.click('.modal.in .modal-footer .devui-btn')
        await asyncio.sleep(5)
        page_list = await self.browser.pages()
        await page_list[-1].setViewport({'width': self.width, 'height': self.height})
        return page_list[-1]

    async def close_page(self):
        page_list = await self.browser.pages()
        if len(page_list) > 1:
            page = page_list[-1]
            if page.url != self.url:
                await page.close()

    async def api_explorer_task(self):
        await asyncio.sleep(3)
        html = str(await self.task_page.JJeval('.userInfo', '(els) => els.map(el => el.outerHTML)'))
        if html.find('English') != -1:
            items = await self.task_page.querySelectorAll('.userInfo')
            await items[1].hover()
            await asyncio.sleep(2)
            await self.task_page.click('.cdk-overlay-container .dropdown-item')
            await asyncio.sleep(5)

        await self.task_page.click('#debug')
        await asyncio.sleep(3)

    async def api2_explorer_task(self):
        _url = 'https://apiexplorer.developer.huaweicloud.com/apiexplorer/doc?product=DevStar&api=ListPublishedTemplates'
        await self.task_page.goto(_url, {'waitUntil': 'load'})
        await self.api_explorer_task()

    async def dev_star_task(self):
        await asyncio.sleep(2)
        await self.task_page.waitForSelector('#confirm-download-btn', {'visible': True})
        await self.task_page.click('.template-dynamic-paramter-title .devui-btn')
        await asyncio.sleep(2)
        await self.task_page.click('#confirm-upload-btn')
        await asyncio.sleep(3)

    async def view_code_task(self):
        await asyncio.sleep(10)
        await self.task_page.click('#code-template-cards .card-width:nth-child(2) .code-template-card-title')
        await asyncio.sleep(2)

    async def open_code_task(self):
        await asyncio.sleep(5)
        items = await self.task_page.querySelectorAll('div.devui-table-view tbody tr')
        if items and len(items):
            await self.task_page.evaluate(
                '''() =>{ document.querySelector('div.devui-table-view tbody tr:nth-child(1) td:nth-child(8) i.icon-more-operate').click(); }''')
            await asyncio.sleep(1)
            await self.task_page.evaluate(
                '''() =>{ document.querySelector('ul.dropdown-menu li:nth-child(5) .devui-btn').click(); }''')
            await asyncio.sleep(20)

    async def open_ide_task(self):
        await asyncio.sleep(5)
        try:
            await self.task_page.click('.region-modal-button-content .region-modal-button-common')
            await asyncio.sleep(1)
        except Exception as e:
            self.logger.debug(e)

        await asyncio.sleep(3)
        await self.task_page.click(
            '.trial-stack-info .trial-stack:nth-child(1) .stack-content .stack-position .devui-btn')
        await asyncio.sleep(10)

    async def push_code_task(self):
        if self.git:
            now_time = time.strftime('%Y-%m-%d %H:%M:%S')
            cmd = [
                'cd /tmp',
                'git config --global user.name "caoyufei" && git config --global user.email "atcaoyufei@gmail.com"',
                f'git clone {self.git}',
                'cd /tmp/crawler',
                f'echo "{now_time}" >> time.txt',
                "git add .",
                "git commit -am 'time'",
                "git push origin master",
            ]
            os.system(' && '.join(cmd))
            os.system('rm -rf /tmp/crawler')
            await asyncio.sleep(1)

    async def week_new_compile_build(self):
        await asyncio.sleep(2)
        await self.task_page.waitForSelector('.devui-layout-main-content', {'visible': True})
        await self.task_page.click('.devui-layout-main-content #create_new_task')
        await asyncio.sleep(1)
        await self.task_page.click('.button-group .devui-btn-stress')
        await asyncio.sleep(5)
        template = await self.task_page.querySelectorAll('.template-content li.template-item')
        await template[3].click()
        await asyncio.sleep(1)
        await self.task_page.click('.button-group .devui-btn-stress')

        await asyncio.sleep(5)
        card_list = await self.task_page.querySelectorAll('.task-detail-cardlist .card-li')
        await card_list[2].hover()
        await asyncio.sleep(1)
        await self.task_page.click('.task-detail-cardlist .card-li:nth-child(3) .add-btn')
        await asyncio.sleep(2)
        await self.task_page.click('.button-group .devui-btn-stress')
        await asyncio.sleep(2)

    async def compile_build_task(self):
        await asyncio.sleep(1)
        node = 'div.devui-table-view tbody tr:nth-child(1) .operation-btn-section .devui-btn:nth-child(1)'
        await self.task_page.evaluate('''() =>{ document.querySelector('%s').click(); }''' % node)
        await asyncio.sleep(1)

        node = 'ul.devui-dropdown-menu li:nth-child(1) a'
        await self.task_page.evaluate('''() =>{ document.querySelector('%s').click(); }''' % node)
        await asyncio.sleep(2)
        await self.task_page.click('.modal-footer .devui-btn-primary')
        await asyncio.sleep(8)

    async def check_code_task(self):
        await asyncio.sleep(5)
        task_list = await self.task_page.querySelectorAll('.devui-table tbody tr')
        task_id = await task_list[0].Jeval('.task-card-name span', "el => el.getAttribute('id')")
        task_id = task_id.replace('task_name', 'task_execute')
        if await self.task_page.querySelector(f'#{task_id}'):
            await self.task_page.click(f'#{task_id}')
        else:
            btn_list = await self.task_page.querySelectorAll('.devui-btn-text-dark')
            await btn_list[0].click()
            await asyncio.sleep(1)
            await self.task_page.click(f'#{task_id}')
        await asyncio.sleep(5)

    async def week_new_deploy(self):
        await asyncio.sleep(2)
        await self.task_page.waitForSelector('.devui-layout-operate', {'visible': True})
        await self.task_page.click('.devui-layout-operate #taskCreate')
        await asyncio.sleep(1)
        await self.task_page.click('.step-group .devui-btn-stress')
        await asyncio.sleep(5)

        template_list = await self.task_page.querySelectorAll('.template-list .template-item')
        await template_list[1].click()
        await asyncio.sleep(0.5)
        await self.task_page.click('.step-group .devui-btn-stress')
        await asyncio.sleep(3)
        items = await self.task_page.querySelectorAll('.category-wrapper ul.devui-nav li')
        await items[4].click()
        await asyncio.sleep(3)

        card_list = await self.task_page.querySelectorAll('.task-detail-cardlist .card-li')
        await card_list[0].hover()
        await asyncio.sleep(0.5)
        await self.task_page.click('.task-detail-cardlist .card-li:nth-child(1) .add-btn')
        await asyncio.sleep(1)

        link_list = await self.task_page.querySelectorAll('.marked-text .devui-link')
        await link_list[1].click()

        await asyncio.sleep(10)
        page_list = await self.browser.pages()
        await page_list[-1].setViewport({'width': self.width, 'height': self.height})
        new_page = page_list[-1]
        await asyncio.sleep(2)
        await new_page.type('input.input-textarea-cn', self.username)
        await asyncio.sleep(0.5)
        await new_page.click('.btn-box .devui-btn-stress')
        await asyncio.sleep(2)
        await new_page.close()

        await self.task_page.click('#DeploymentGroup_groupId_button')
        await asyncio.sleep(2)
        await self.task_page.click('.deployment-select')
        await asyncio.sleep(0.5)
        await self.task_page.click('.devui-dropdown-item:nth-child(1)')
        await asyncio.sleep(0.5)
        await self.task_page.type('div#SingleLineText_port_to_stop input', ''.join(random.choices(string.digits, k=4)))
        await asyncio.sleep(0.5)
        await self.task_page.click('.deployman-create-content__button-group .devui-btn-primary')
        await asyncio.sleep(3)

    async def deploy_task(self):
        await asyncio.sleep(3)
        await self.task_page.click('#rf-task-execute')
        await asyncio.sleep(3)

    async def run_test(self):
        await self._close_test()
        await self.task_page.waitForSelector('div.devui-table-view', {'visible': True})
        # string = await self.task_page.Jeval('div.devui-table-view tbody tr:nth-child(1) td:nth-child(12)',
        #                                     'el => el.outerHTML')
        # print(string)

        await self.task_page.evaluate(
            '''() =>{ document.querySelector('div.devui-table-view tbody tr:nth-child(1) td:nth-child(12) i.icon-run').click(); }''')

        await asyncio.sleep(5)

    async def api_test_task(self):
        await asyncio.sleep(2)
        await self._close_test()
        await self._tab_api_test()
        await self.task_page.evaluate(
            '''() =>{ document.querySelector('div.devui-table-view tbody tr:nth-child(1) i.icon-run').click(); }''')
        await asyncio.sleep(5)

    async def week_new_pipeline(self):
        await asyncio.sleep(2)
        await self.task_page.click('#createPipeline')
        await asyncio.sleep(1)
        await self.task_page.click('.content .devui-dropup')
        await asyncio.sleep(0.5)
        await self.task_page.click('.devui-dropdown-item:nth-child(1)')
        await asyncio.sleep(0.5)
        await self.task_page.click('.pipeline-edit-tab .devui-btn-primary')
        await asyncio.sleep(0.5)

        dropdowns = await self.task_page.querySelectorAll('.devui-dropup')
        for dropdown in dropdowns:
            await dropdown.click()
            await asyncio.sleep(1)
            dropdown_item = await dropdown.querySelectorAll('.devui-dropdown-item')
            await dropdown_item[0].click()
            await asyncio.sleep(0.5)

        await self.task_page.click('.pipeline-edit-tab .devui-btn-primary')
        await asyncio.sleep(1)
        await self.task_page.click('.pipeline-edit-tab .devui-btn-primary')
        await asyncio.sleep(5)

    async def pipeline_task(self):
        await asyncio.sleep(1)
        await self.task_page.evaluate(
            '''() =>{ document.querySelector('div.devui-table-view tbody tr:nth-child(1) .icon-run').click(); }''')
        await asyncio.sleep(1)
        await self.task_page.click('.modal.in .devui-btn-primary')
        await asyncio.sleep(1)
        await self.task_page.click('.modal.in .devui-btn-primary')
        await asyncio.sleep(1)

        # dropdowns = await self.task_page.querySelectorAll('div.source-value')
        # dropup = await dropdowns[0].querySelectorAll('.devui-dropup')
        # await dropup[1].click()
        # await asyncio.sleep(2)
        # dropdown_item = await dropup[1].querySelectorAll('.devui-dropdown-item')
        # await dropdown_item[0].click()
        # await asyncio.sleep(0.5)
        # await self.task_page.click('.modal.in .devui-btn-primary')
        await asyncio.sleep(5)

    async def week_new_project(self):
        await asyncio.sleep(5)
        try:
            notice = await self.task_page.querySelector('#declaration-notice')
            if notice:
                btn_list = await self.task_page.querySelectorAll('.quick-create-phoenix .devui-btn')
                await btn_list[1].click()
                await asyncio.sleep(1)
                await self.task_page.click('#declaration-notice div.devui-checkbox label')
                await asyncio.sleep(1)
                await self.task_page.click('#declaration-notice .devui-btn.devui-btn-primary')
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.debug(e)

        try:
            btn_list = await self.task_page.querySelectorAll('.quick-create-phoenix .devui-btn')
            await btn_list[0].click()
            await asyncio.sleep(2)
        except Exception as e:
            await self.send_photo(self.task_page, 'week_new_project')
            self.logger.exception(e)
            await self.close()
            self.cancel = True

    async def week_new_git(self):
        await asyncio.sleep(5)
        no_data = await self.task_page.querySelector('.new-list .no-data')
        await self.task_page.waitForSelector('.pull-right', {'visible': True})
        await self.task_page.click('.pull-right .devui-btn-primary')
        await asyncio.sleep(1)
        git_name = ''.join(random.choices(string.ascii_letters, k=6))
        if not no_data:
            git_name = 'crawler'
        await self.task_page.type('#rname', git_name)
        await asyncio.sleep(0.5)

        btn_list = await self.task_page.querySelectorAll('.new-repo-row-center:nth-child(1) .devui-checkbox')
        await btn_list[2].click()

        await self.task_page.click('#newAddRepoBtn')
        await asyncio.sleep(8)

        git_list = await self.task_page.querySelectorAll('.devui-table tbody tr')
        if git_list and len(git_list) and git_name == 'crawler':
            await self.task_page.click('#repoNamecrawler')
            await asyncio.sleep(10)
            git_url = await self.task_page.Jeval('.clone-url input', "el => el.getAttribute('title')")
            _user = self.parent_user if self.parent_user else self.username
            git_url = git_url.replace('git@', f'https://{_user}%2F{self.username}:{self.password}@')
            self.git = git_url.replace('com:', 'com/')
            self.logger.info(self.git)

    async def week_new_code_check(self):
        await self.task_page.waitForSelector('.pull-right', {'visible': True})
        await self.task_page.click('.pull-right .devui-btn-primary')
        await asyncio.sleep(8)
        btn = await self.task_page.querySelector('#codecheck-new-task-btn-0')
        if btn:
            await btn.click()
            await asyncio.sleep(1)
            await self.task_page.click('.btn-wrap .devui-btn-primary')
            await asyncio.sleep(5)

    async def upload_task(self):
        await asyncio.sleep(3)
        # items = await self.task_page.querySelectorAll('')

        await self.task_page.click('#releasemanUploadDrop tbody tr:nth-child(1) td a.column-link')
        await asyncio.sleep(3)
        await self.task_page.waitForSelector('#upload_file', {'visible': True})
        f = await self.task_page.querySelector('#releaseman-file-select')
        await f.uploadFile(__file__)
        await asyncio.sleep(3)

    async def new_test_task(self):
        await asyncio.sleep(2)
        await self.task_page.click('#global-guidelines .icon-close')
        await asyncio.sleep(1)
        await self.task_page.click('.guide-container .icon-close')
        await asyncio.sleep(1)
        await self.task_page.waitForSelector('div.create-case', {'visible': True})
        await self.task_page.click('div.create-case')
        await asyncio.sleep(5)
        await self.task_page.type('#caseName', ''.join(random.choices(string.ascii_letters, k=6)))
        await self.task_page.click('div.footer .devui-btn-stress')
        await asyncio.sleep(5)

    async def week_new_api_test_task(self):
        await asyncio.sleep(2)
        await self._close_test()
        await self._tab_api_test()
        await self.task_page.waitForSelector('div.create-case', {'visible': True})
        await self.task_page.click('div.create-case')
        await asyncio.sleep(2)
        await self.task_page.type('#caseName', ''.join(random.choices(string.ascii_letters, k=6)))
        await self.task_page.click('div.footer .devui-btn-stress')
        await asyncio.sleep(3)

    async def new_new_api_task(self):
        await asyncio.sleep(15)
        self.logger.debug(self.task_page.url)

    async def run_api_task(self):
        await asyncio.sleep(3)
        await self.task_page.click('div.ti-intro-modal .ti-btn-danger')
        await asyncio.sleep(3)
        await self.task_page.click('#send')
        await asyncio.sleep(2)
        await self.task_page.click('.pull-left .cti-button')
        await asyncio.sleep(5)
        await self.task_page.click('.pull-right.mr10.cti-button')
        await asyncio.sleep(5)
        await self.task_page.click('.ti-btn-danger.ml10.ng-binding')

    async def new_fun_task(self):
        url = self.task_page.url
        if url.find('serverless/dashboard') == -1:
            url = f'{url}#/serverless/dashboard'
            await self.task_page.goto(url, {'waitUntil': 'load'})

        await asyncio.sleep(2)
        try:
            await self.task_page.click('#rightWrap .ant-row .ant-btn')
            await asyncio.sleep(3)
            await self.task_page.type('#name', ''.join(random.choices(string.ascii_letters, k=6)), {'delay': 30})
            await asyncio.sleep(3)
            await self.task_page.click('.preview .ant-btn-primary')
            await asyncio.sleep(5)
        except Exception as e:
            self.logger.warning(e)
        finally:
            return

    async def fast_dev_star(self):
        await asyncio.sleep(5)
        await self.task_page.click('.code-template-codebase-right-operations-panel .devui-btn-common')
        # await asyncio.sleep(1)
        # await self.task_page.click('.operation-next')
        await asyncio.sleep(3)
        await self.task_page.click('#deploy-btn')

        await asyncio.sleep(15)


    async def delete_function(self):
        page = await self.browser.newPage()
        url_list = ['https://console.huaweicloud.com/functiongraph/?region=cn-north-4#/serverless/functionList',
                    'https://console.huaweicloud.com/functiongraph/?region=cn-south-1#/serverless/functionList']
        for _url in url_list:
            await page.goto(_url, {'waitUntil': 'load'})
            await page.setViewport({'width': self.width, 'height': self.height})
            await asyncio.sleep(5)
            elements = await page.querySelectorAll('td[style="white-space: normal;"]')
            for element in elements:
                a_list = await element.querySelectorAll('a.ti3-action-menu-item')
                # content = str(await (await element.getProperty('textContent')).jsonValue()).strip()
                if len(a_list) == 2:
                    try:
                        await a_list[1].click()
                        await asyncio.sleep(1)
                        await page.type('.modal-confirm-text input[type="text"]', 'DELETE')
                        await asyncio.sleep(1)
                        await page.click('.ti3-modal-footer .ti3-btn-danger')
                        await asyncio.sleep(1)
                    except Exception as e:
                        self.logger.exception(e)

        await page.close()
        await asyncio.sleep(1)

    async def check_project(self):
        page = await self.browser.newPage()
        domains = ['https://devcloud.huaweicloud.com', 'https://devcloud.cn-north-4.huaweicloud.com']
        try:
            for domain in domains:
                url = f'{domain}/projects/v2/project/list?sort=&search=&page_no=1&page_size=40&project_type=&archive=1'
                res = await page.goto(url, {'waitUntil': 'load'})
                data = await res.json()
                if data.get('error') or not data.get('result'):
                    await asyncio.sleep(1)
                    continue

                projects = data['result']['project_info_list']
                self.home_url = domain

                if len(projects) > 0:
                    self.create_done = False
                    break
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(e)
        finally:
            await page.close()
            self.logger.info(self.create_done)

    async def delete_project(self):
        page = await self.browser.newPage()
        domains = ['https://devcloud.huaweicloud.com', 'https://devcloud.cn-north-4.huaweicloud.com']
        for i in range(3):
            try:
                for domain in domains:
                    url = f'{domain}/projects/v2/project/list?sort=&search=&page_no=1&page_size=40&project_type=&archive=1'
                    res = await page.goto(url, {'waitUntil': 'load'})
                    data = await res.json()
                    if data.get('error') or not data.get('result'):
                        continue

                    for item in data['result']['project_info_list']:
                        try:
                            self.logger.warning(f"delete project {item['name']}")
                            delete_url = f"{domain}/projects/project/{item['project_id']}/config/info"
                            await page.goto(delete_url, {'waitUntil': 'load'})
                            await asyncio.sleep(2)
                            btn_list = await page.querySelectorAll('.modal-footer .btn')
                            if len(btn_list) == 2:
                                await btn_list[1].click()
                                await asyncio.sleep(1)

                            await page.click('.form-container .margin-right-s .devui-btn:nth-child(1)')
                            await asyncio.sleep(2)
                            await page.type('#deleteProject .projectInput', item['name'])
                            await asyncio.sleep(0.5)
                            await page.click('.dialog-footer .devui-btn-primary')
                            await asyncio.sleep(1)
                        except Exception as e:
                            self.logger.error(e)
                break
            except Exception as e:
                self.logger.error(e)
                await asyncio.sleep(5)
        await page.close()

    async def delete_api(self):
        page = await self.browser.newPage()
        try:
            await page.goto('https://console.huaweicloud.com/apig/?region=cn-north-4#/apig/multiLogical/openapi/list',
                            {'waitUntil': 'load'})
            await page.setViewport({'width': self.width, 'height': self.height})
            await asyncio.sleep(10)
            elements = await page.querySelectorAll('#openapi_list tr')
            if len(elements) < 2:
                return

            # 下线
            await page.click('#openapi_list tr:nth-child(1) th:nth-child(1)')
            await asyncio.sleep(0.5)
            await page.click('.apiList-groups .cti-button:nth-child(3) .cti-btn-container')
            await asyncio.sleep(1)
            await page.click('.ti-modal-dialog .cti-button:nth-child(1) .cti-btn-container')
            await asyncio.sleep(2)

            # 删除
            await page.click('#openapi_list tr:nth-child(1) th:nth-child(1)')
            await asyncio.sleep(0.5)
            await page.click('.apiList-groups .cti-button:nth-child(4) .cti-btn-container')
            await asyncio.sleep(3)
            await page.type('#deleteContent-text', 'DELETE')
            await asyncio.sleep(0.5)
            await page.click('.ti-modal-dialog .cti-button:nth-child(1) .cti-btn-container')
            await asyncio.sleep(2)
        except Exception as e:
            self.logger.debug(e)
        finally:
            await page.close()

    async def delete_api_group(self):
        page = await self.browser.newPage()
        try:
            await page.goto('https://console.huaweicloud.com/apig/?region=cn-north-4#/apig/multiLogical/openapi/group',
                            {'waitUntil': 'load'})
            await page.setViewport({'width': self.width, 'height': self.height})
            await asyncio.sleep(8)
            elements = await page.querySelectorAll('#openapi_group tbody tr')
            if len(elements) < 1:
                return

            await page.click('#openapi_group tbody tr:nth-child(1) td:nth-child(1) a')
            await asyncio.sleep(2)
            await page.click('.cti-fl-right .cti-button:nth-child(4) .cti-btn-container')
            await asyncio.sleep(1)
            await page.type('#tiny-text', 'DELETE')
            await asyncio.sleep(0.5)
            await page.click('#delG')
            await asyncio.sleep(2)
        except Exception as e:
            self.logger.debug(e)
        finally:
            await page.close()

    async def _close_test(self):
        try:
            await asyncio.sleep(1)
            await self.task_page.click('#global-guidelines .icon-close')
            await asyncio.sleep(2)
            await self.task_page.click('.guide-container .icon-close')
            await asyncio.sleep(1)
        except Exception as e:
            self.logger.debug(e)

    async def _tab_api_test(self):
        await asyncio.sleep(1)
        await self.task_page.waitForSelector('#testtype_1')
        await self.task_page.click('#testtype_1')
        await asyncio.sleep(1)

    async def sign_post(self):
        tid_list = [87703, 87513, 87948, 87424, 87445, 87587, 87972, 87972]
        n = random.randint(1, 2)
        for i in range(n):
            tid = random.choice(tid_list)
            await self.page.goto(f'https://bbs.huaweicloud.com/forum/thread-{tid}-1-1.html', {'waitUntil': 'load'})
            await self.page.waitForSelector('#fastpostsubmit')
            content = random.choice(
                ['666', '回帖送码豆', '论坛回帖送码豆喽'])
            await self.page.evaluate(
                '''() =>{ ue.setContent('<p>%s</p>'); }''' % content)
            await asyncio.sleep(1)
            await self.page.click('#fastpostsubmit')
            await asyncio.sleep(5)

    async def post_reply(self):
        await self.page.goto('https://bbs.huaweicloud.com/forum/thread-89722-1-1.html', {'waitUntil': 'load'})
        await self.page.waitForSelector('#fastpostsubmit')
        content = '#2020年终盛典# 我很期待这次盛典，祝盛典圆满成功！顺利召开！'
        await self.page.evaluate(
            '''() =>{ ue.setContent('<p>%s</p>'); }''' % content)
        await asyncio.sleep(1)
        await self.page.click('#fastpostsubmit')
        await asyncio.sleep(10)

        await self.page.goto('https://bbs.huaweicloud.com/forum/thread-89742-1-1.html', {'waitUntil': 'load'})
        await self.page.waitForSelector('#fastpostsubmit')
        content = ' #我和华为云的这一年#这一年是我和华为云相识的第一年，知道了华为云有很多课程，大拿讲课，受益颇丰。'
        await self.page.evaluate(
            '''() =>{ ue.setContent('<p>%s</p>'); }''' % content)
        await asyncio.sleep(1)
        await self.page.click('#fastpostsubmit')
        await asyncio.sleep(5)

        # await self.page.goto('https://bbs.huaweicloud.com/forum/thread-80376-1-1.html', {'waitUntil': 'load'})
        # await self.page.waitForSelector('#fastpostsubmit')
        # await self.page.evaluate('''() =>{ document.querySelector('#tabeditor-2').click(); }''')
        # await asyncio.sleep(1)
        # await self.page.click('#tabeditor-2')
        # content = random.choice(
        #     [
        #         '![1024](https://bbs-img-cbc-cn.obs.cn-north-1.myhuaweicloud.com/data/attachment/forum/202010/09/204951b8y0xls2nopvc6az.png)',
        #         '![1024](https://bbs-img-cbc-cn.obs.cn-north-1.myhuaweicloud.com/data/attachment/forum/202010/09/161504wwp2tknsrfkzytrm.png)',
        #         '![1024](https://bbs-img-cbc-cn.obs.cn-north-1.myhuaweicloud.com/data/attachment/forum/202010/09/173512tnrpfkysqadqtlee.png)',
        #         '![1024](https://bbs-img-cbc-cn.obs.cn-north-1.myhuaweicloud.com/data/attachment/forum/202010/09/162825q3widemjdlppcjb0.png)',
        #         '![1024](https://bbs-img-cbc-cn.obs.cn-north-1.myhuaweicloud.com/data/attachment/forum/202010/10/111533ab4neej10wtrbmm6.png)',
        #     ])
        # await self.page.type('.textarea', content, {'delay': 30})
        # # await self.page.evaluate('''() =>{ document.querySelector('.textarea').value = '%s'; }''' % content)
        # # await self.page.evaluate('''() =>{ document.querySelector('#mditorBox').value = '%s'; }''' % content)
        # await asyncio.sleep(1)
        # await self.page.click('#fastpostsubmit')
        # await asyncio.sleep(5)

    # HDC flag 读书签到 3月23日-4月20日，累计29天
    async def hdc_read(self):
        await self.page.goto(os.environ.get('FLAGURL'), {'waitUntil': 'load'})
        await self.page.waitForSelector('#fastpostsubmit')
        await asyncio.sleep(1)
        await self.page.click('#tabeditor-2')
        content = random.choice(
                [
                    '每天坚持打卡', 
                    '实现flag，打卡mark', 
                    '坚持继续打卡~~', 
                    '打卡++1', 
                    'flag达成', 
                    '记录一下', 
                    'mark今天的打卡', 
                    '打卡，坚持不停',
                    '继续打卡'
                ])
        await self.page.type('.textarea', content, {'delay': 30})
        await asyncio.sleep(1)
        await self.page.click('#fastpostsubmit')
        await asyncio.sleep(30)
    
    # 【我要去HDC2021①】口令盖楼，周边、码豆、门票每周送！ 活动时间：3月23日-4月20日
    async def hdc_floor(self):
        await self.page.goto('https://bbs.huaweicloud.com/forum/thread-115425-1-1.html', {'waitUntil': 'load'})
        await self.page.waitForSelector('#fastpostsubmit')
        await asyncio.sleep(1)
        await self.page.click('#tabeditor-2')
        content = random.choice(
                [
                    '华为开发者大会2021（Cloud）是华为面向ICT(信息与通信)领域全球开发者的年度旗舰活动。', 
                    '华为云IoT致力于提供极简接入、智能化、安全可信等全栈全场景服务和开发、集成、托管、运营等一站式工具服务。', 
                    '华为云IoT边缘（IoT Edge），是边缘计算在物联网行业的应用。IoT Edge 在靠近物或数据源头的边缘侧，融合网络、计算、存储、应用核心能力的开放平台，就近提供计算和智能服务，满足行业在实时业务、应用智能、安全与隐私保护等方面的基本需求。', 
                    '华为云IoT设备接入服务IoTDA（IoT Device Access）是华为云的物联网平台，提供海量设备连接上云、设备和云端双向消息通信、批量设备管理、远程控制和监控、OTA升级、设备联动规则等能力，并可将设备数据灵活流转到华为云其他服务，帮助物联网行业用户快速完成设备联网及行业应用集成。', 
                    '华为云IoT设备发放 IoTDP通过设备发放服务，您可以轻松管理跨多区域海量设备的发放工作，实现单点发放管理，设备全球上线的业务目的。', 
                    '华为云IoT全球SIM联接（Global SIM Link）提供无线蜂窝物联网流量和eSIM/vSIM按需选网，享受当地资费，为客户提供一点接入、全球可达的一站式流量管理服务。', 
                    '华为云IoT数据分析服务IoTA基于物联网资产模型，整合IoT数据集成、清洗、存储、分析、可视化，为IoT数据开发者提供一站式服务，降低开发门槛，缩短开发周期，快速实现IoT数据价值变现。',
                    '华为轻量级操作系统 LiteOS，驱动万物感知、互联、智能，可广泛应用于面向个人、家庭和行业的物联网产品和解决方案。',
                    '华为云IoT应用场景——智慧抄表：围绕城市工商户和居民水表、气表等智能远传抄表场景，结合NB-IoT技术，提供包括IoT平台、企业智能、应用服务、安全管理等端到端优化的云服务能力，令企业运营更高效、居民生活更便捷。',
                    '华云IoT应用场景——智慧路灯：随着城镇化建设的推进，城市照明面临着数量多、能耗高、管理难、维护成本高的挑战。华为智慧路灯解决方案，提出统一管理各城市区域内的路灯，实现按需照明，深化节能，提升城市安全氛围，为城市发展提供绿动力。',
                    '华为云IoT应用场景——智慧环保：基于华为IoT云服务的智慧环境监测解决方案，通过NB-IoT一跳方式采集空气质量监测数据，统一汇聚，数据真实、可靠，为政府决策提供有效数据支撑。',
                    '华为云IoT应用场景——智慧停车：通过NB-IoT车检器实时采集车位数据，智慧停车系统可实时监测各个车位使用状态，提供车位查询、车位引导、车位预定、反向找车、智能管理等功能，真正让用户有更好的停车体验，提升城市居民满意度。',
                    '华为云IoT应用场景——智慧安防：基于物联网平台实现园区周界、消防各类传感器的统一接入管理，跨系统联动，融合智能化图像搜索、大数据分析等多种智慧安防能力，支持可视化指挥调度和管理，实现事前主动预防， 事中快速管控，事后高效复盘。',
                    '华为云IoT应用场景——智慧资产管理：基于物联网平台和RFID等物联网技术将园区物理资产数字化，实时监控资产动态，快速盘点亿级资产，降低审计成本，减少设备丢失风险。实时统计资产位置和使用率情况，实现部门间共享和费用结算，高效利用资产设备，减少资产闲置。',
                    '华为云IoT应用场景——数字化高速公路：高速公路是综合交通运输体系的重要组成部分，为适应高速公路管理能力提升的要求，提供综合交通数字化管理平台，完整呈现实时高速路交通状态，及时准确的发现拥堵、事故、道路异常等交通事件，提升高速管理效率，诱导合理出行。',
                    '华为云IoT应用场景——城市道路数字化改造：在城市路口和关键路段采集视频和多种路侧传感器信息，多层次应用智能算法，实现非现场执法和城市道路交通的优化能力。',
                    '华为云IoT应用场景——园区自动驾驶：基于道路感知服务，在相对封闭的园区或停车场，与车厂自动驾驶技术配合实现限定区域内的自动驾驶，推动自动驾驶技术落地，切实解决客户园区内交通、停车等需求。',
                    '华为云IoT城市物联服务台助力鹰潭城市物联网产业竞争力提升，并着力打造城市名片。目前鹰潭网络建设、公共服务平台建设、示范应用建设领跑全国，已有30+类物联网应用，15万+设备接入。',
                    '华为云IoT携手兆邦基集团，基于园区物联网服务在深圳前海打造高效、智能、绿色、安全的科技大厦，实现楼宇设备全连接、数据全融合、场景全联动、调度全智能，有效节约能耗15%。',
                    '基于华为云IoT全栈云服务，武汉拓宝科技股份有限公司以云计算为核心实现海量数据的汇总处理，提升管理效率，随时随地接受火警，集中管理设备，大大降低了消防实施成本，设备无线联网，电池供电，不需布线，无线覆盖广，平台云端部署。',
                    '深圳市泛海三江电子股份有限公司基于华为云IoT全栈云服务，实现了消防从烟感探测器这个“哨兵”到消防中心的“指挥部”全程打通，从而突破消防产品单一性销售弊端，开拓全面的消防服务渠道。',
                    '基于华为云IoT提供的路网数字化服务，都汶高速采用摄像头、雷达等多维度数据采集，在不受雨雾遮挡影响、不新增路灯的情况下，实现全天候实时感知，并能对车辆位置、速度等进行准确检测，实现多种车路协同场景的安全预警。',
                    '基于华为云IoT设备接入管理服务，SKG实现了手机APP-按 摩仪-云端的智能交互。用户可通过APP选择适合的按 摩功能，还可从云端模式库中下载不同手法的软件包，一键下载、自动安装。',
                    '华为云&中创瀚维携手打造了以自动割胶系统为核心的智慧胶园，每棵胶树上配置自动割胶机，通过云端统一管控，并将割胶机的精准机械仿形与云端实时感知控制相结合，实现对不同形状胶树的标准0.01mm厚度的精准割胶。',
                ])
        await self.page.type('.textarea', content, {'delay': 30})
        await asyncio.sleep(1)
        await self.page.click('#fastpostsubmit')
        await asyncio.sleep(30)
