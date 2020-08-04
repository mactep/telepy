import aiohttp
import asyncio
import logging

class Telegram:
    def __init__(self, token, session=None):
        self.token = token
        self.logger = logging.getLogger('Telegram')

        if session is None:
            self.logger.debug('Creating new session')
            self.session = aiohttp.ClientSession()
        else:
            self.logger.debug('Using user provided session')
            self.session = session

    async def __aenter__(self):
        self.logger.debug('enter')

    async def __aexit__(self, exc_type, exc, tb):
        # TODO: only close the session if it's not user provided
        self.logger.debug('Closing session')
        await self.session.close()

    async def api_call(self, method, **kwargs):
        self.logger.debug("Calling telegram api '{}'".format(method))
        endpoint = "https://api.telegram.org/bot{}/{}".format(self.token, method)
        async with self.session.get(endpoint, params=kwargs) as response:
            json_response = await response.json()

            if response.status == 404:
                self.logger.error('Error in the api call: invalid method or token')

            elif not json_response.get('ok') or response.status != 200:
                self.logger.error('Error in the api call\n {}'.format(str(response)))

            else:
                return json_response

    async def get_update(self, update_id):
        self.logger.debug("Polling update id '{}'".format(update_id))
        return await self.api_call('getUpdates', offset=update_id)

    async def poll(self, sleep_interval=10, update_id=0):
        while True:
            response = await self.get_update(update_id)

            if response is None:
                self.logger.debug('Malformed response, waiting for the api...')
                await asyncio.sleep(15)
                continue

            result = response.get('result')
            if len(result):
                update_id = result[-1].get('update_id') + 1

            await asyncio.sleep(sleep_interval)
