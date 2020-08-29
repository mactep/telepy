import asyncio

from telepy.client import Telegram

t = Telegram(TOKEN)

@t.on("test")
async def butter_handler(chat_id, *args):
    await t.send_message(chat_id, "You passed")

async def main_update():
    async with t:
        await t.poll()


async def main_webhook():
    async with t:
        await t.set_webhook(HOST/PATH, CERTIFICATE)
        await t.run_webhook_server(CERTIFICATE, KEY, port=PORT)

        await t.run_forever()

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main_update())
    # loop.run_until_complete(main_webhook())

except KeyboardInterrupt:
    pass

finally:
    loop.run_until_complete(asyncio.sleep(1))
    loop.close()
