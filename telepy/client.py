import aiohttp
import asyncio
import logging
import ssl

from aiohttp import web
from pyee import AsyncIOEventEmitter

class Telegram(AsyncIOEventEmitter):
    def __init__(self, token, session=None):
        AsyncIOEventEmitter.__init__(self)

        self.logger = logging.getLogger('Telegram')

        self.token = token
        self.update_id = 0

        self.runner = None
        self.webhook = False
        self.webhook_url = ''


        if session is None:
            self.logger.debug('Creating new session')
            self.session = aiohttp.ClientSession()
            self.user_provided_session = False
        else:
            self.logger.debug('Using user provided session')
            self.session = session
            self.user_provided_session = True

    async def __aenter__(self):
        self.logger.debug('enter')

    async def _close(self):
        if not self.user_provided_session:
            self.logger.debug('Closing session')
            await self.session.close()

        if self.webhook and self.runner is not None:
            await self.runner.cleanup()

    async def __aexit__(self, exc_type, exc, tb):
        await self._close()

    async def __request(self, method, url, payload={}):
        if method == "GET":
            return await self.session.get(url, params=payload)

        if method == "POST":
            return await self.session.post(url, data=payload)

    async def api_call(self, endpoint, method="GET", **kwargs):
        self.logger.debug("Calling telegram api '{}'".format(endpoint))
        url = "https://api.telegram.org/bot{}/{}".format(self.token, endpoint)

        response = await self.__request(method, url, payload=kwargs)
        json_response = await response.json()

        if response.status == 404:
            self.logger.error('Error in the api call: invalid endpoint or token')

        elif not json_response.get('ok') or response.status != 200:
            self.logger.error('Error in the api call\n {}'.format(str(response)))

        else:
            return json_response

    async def get_update(self, update_id):
        self.logger.debug("Polling update id '{}'".format(update_id))
        return await self.api_call('getUpdates', offset=update_id)

    async def set_webhook(self, url, cert, **kwargs):
        self.logger.debug('Setting webhook')

        with open(cert, 'rb') as f:
            data = {'url': url, 'certificate': f}
            response = await self.api_call("setWebhook", method="POST", **data)

        self.webhook = True
        self.webhook_url = url

        return response

    async def get_webhook_info(self):
        return await self.api_call('getWebhookInfo')

    async def send_message(self, chat_id, text):
        return await self.api_call('sendMessage', chat_id=chat_id, text=text)

    async def __parse_update(self, update):
        if type(update) == web.Request and update.content_type == "application/json":
            update = await update.json()

        self.logger.debug('Parsing update')
        message = update.get('message')
        if message:
            text = message.get('text')
            if text:
                chat_id = message['chat']['id']
                if text.startswith('/'):
                    command, *args = text[1:].split()
                    self.emit(command, chat_id, *args)

        return web.Response()

    async def poll(self, sleep_interval=10):
        if self.webhook:
            self.logger.warn("Webhook defined, returning...")
            return

        while True:
            response = await self.get_update(self.update_id)

            result = response.get('result')
            for update in result:
                await self.__parse_update(update)

            await asyncio.sleep(sleep_interval)

    async def run_webhook_server(self, cert, key, port):
        webhook_path = "/{}".format(self.webhook_url.split('/')[1])

        app = web.Application()
        app.add_routes([web.post(webhook_path, self.__parse_update)])

        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(cert, key)

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, host='0.0.0.0', port=port, ssl_context=ssl_context)
        await site.start()

    async def run_forever(self):
        while True:
            await asyncio.sleep(0)
