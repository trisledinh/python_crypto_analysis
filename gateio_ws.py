import asyncio
import os
from gate_ws import Configuration, Connection, WebSocketResponse
from gate_ws.spot import SpotPublicTradeChannel


# define your callback function on message received
async def print_message(conn: Connection, response: WebSocketResponse):
    await asyncio.sleep(1)
    if response.error:
        print('error returned: ', response.error)
        conn.close()
        return
    result = response.result
    side = result['side']
    amount = result['amount']
    price = result['price']
    print('Side: {0}, Amount:{1}, Price: {2}'.format(side, amount, price))


async def main():
    # initialize default connection, which connects to spot WebSocket V4
    # it is recommended to use one conn to initialize multiple channels

    api_key = os.environ.get('gateio_api_key')
    api_secret = os.environ.get('gateio_secret_key')

    conn = Connection(Configuration(api_key=api_key, api_secret=api_secret))

    # subscribe to any channel you are interested into, with the callback function
    channel = SpotPublicTradeChannel(conn, print_message)
    channel.subscribe(["TRX_USDT", "BTC_USDT"])

    # start the client
    await conn.run()


if __name__ == '__main__':
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main())
   loop.close()