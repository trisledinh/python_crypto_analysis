import os
import asyncio
from datetime import datetime, timedelta
import logging
from decimal import Decimal as D
import math

from gate_api import ApiClient, Configuration, Order, SpotApi, OrderBook
from gate_api.exceptions import ApiException, GateApiException

from config import RunConfig
from db_manager import DBManager

logger = logging.getLogger(__name__)

class GateOrder(object):
    def __init__(self, run_config):
        self.run_config = run_config
        self.db = DBManager("localhost", 27018, "", "", "trady")
        self.order_ids = []

    async def create_order(self):
        
        while True:
            await asyncio.sleep(5)
            
            db = self.db
            query = {"Type": "buy", "Status": "0"}

            order_wait = db.read_one("OrderBook", query)

            if order_wait is not None:

                print(order_wait["Pair"])
                ask_pair = order_wait["Pair"]
                ask_side = order_wait["Type"]
                ask_amount = D(order_wait["Amount"])
                ask_price = D(order_wait["Price"])

                self.update_order_status(db)

                config = Configuration(
                key=self.run_config.api_key, secret=self.run_config.api_secret, host=self.run_config.host_used)

                spot_api = SpotApi(ApiClient(config))

                order = Order(currency_pair=ask_pair, side=ask_side,
                            amount=ask_amount, price=ask_price)  # Order |

                currency = ask_pair.split("_")[1]
                try:
                    accounts = spot_api.list_spot_accounts(currency=currency)
                    assert len(accounts) == 1
                    available = D(accounts[0].available)
                    logger.info("Account available: %s %s", str(available), currency)
                    if available < ask_amount:
                        logger.error("Account balance not enough")
                        return
                    # Create an order
                    orderResult = spot_api.create_order(order)
                    print(orderResult)
                    logger.info("order created with id %s, status %s",
                            orderResult.id, orderResult.status)

                    if orderResult.status == 'open':
                        self.order_ids.append({"Id": orderResult.id, "Status": orderResult.status, "Pair": ask_pair})

                        self.update_order_status(db)

                        order_result = spot_api.get_order(orderResult.id, ask_pair)
                        logger.info("order %s filled %s, left: %s", order_result.id,
                                    order_result.filled_total, order_result.left)
                        result = spot_api.cancel_order(order_result.id, ask_pair)
                        if result.status == 'cancelled':
                            logger.info("order %s cancelled", result.id)
                    else:
                        trades = spot_api.list_my_trades(ask_pair, order_id=orderResult.id)
                        assert len(trades) > 0
                        for t in trades:
                            logger.info("order %s filled %s with price %s",
                                        t.order_id, t.amount, t.price)

                    return orderResult
                except GateApiException as ex:
                    print("Gate api exception, label: %s, message: %s\n" %
                        (ex.label, ex.message))
                    break
                except ApiException as e:
                    print("Exception when calling SpotApi->list_order_book: %s\n" % e)
                    break

    def update_order_status(self, db):
        filter = {"Type": "buy", "Status": "0"}
                # Values to be updated.
        newvalues = { "$set": { 'Status': "1" } }
        db.update_one("OrderBook", filter, newvalues)


    def spot_demo_order(self):
        # type: (RunConfig) -> None
        currency_pair = "TRX_USDT"
        currency = currency_pair.split("_")[1]

        # Initialize API client
        # Setting host is optional. It defaults to https://api.gateio.ws/api/v4
        config = Configuration(
            key=self.run_config.api_key, secret=self.run_config.api_secret, host=self.run_config.host_used)
        spot_api = SpotApi(ApiClient(config))
        pair = spot_api.get_currency_pair(currency_pair)
        logger.info("testing against currency pair: " + currency_pair)
        min_quote_amount = pair.min_quote_amount
        fee = D(pair.fee)
        precision = D(pair.precision)

        # get last price
        tickers = spot_api.list_tickers(currency_pair=currency_pair)
        assert len(tickers) == 1
        last_price = D(tickers[0].last)
        order_price = round(last_price - D(50/ math.pow(10, precision)), 5)
        # make sure balance is enough
        order_amount = math.ceil(D(min_quote_amount) / D(order_price) + 1)

        # calculate total amount: value and fee
        total_amount = order_amount * last_price * (1 + fee) 

        accounts = spot_api.list_spot_accounts(currency=currency)
        assert len(accounts) == 1
        available = D(accounts[0].available)
        logger.info("Account available: %s %s", str(available), currency)
        if available < total_amount:
            logger.error("Account balance not enough")
            return

        order = Order(amount=str(order_amount), price=str(order_price),
                    side='buy', currency_pair=currency_pair)
        logger.info("place a spot %s order in %s with amount %s and price %s", order.side, order.currency_pair,
                    order.amount, order.price)

        created = spot_api.create_order(order)
        logger.info("order created with id %s, status %s",
                    created.id, created.status)

        if created.status == 'open':
            order_result = spot_api.get_order(created.id, currency_pair)
            logger.info("order %s filled %s, left: %s", order_result.id,
                        order_result.filled_total, order_result.left)
            result = spot_api.cancel_order(order_result.id, currency_pair)
            if result.status == 'cancelled':
                logger.info("order %s cancelled", result.id)
        else:
            trades = spot_api.list_my_trades(currency_pair, order_id=created.id)
            assert len(trades) > 0
            for t in trades:
                logger.info("order %s filled %s with price %s",
                            t.order_id, t.amount, t.price)

    # Get list currency supported by GateIO


    def get_list_currency(self):
        # Initialize API client
        # Setting host is optional. It defaults to https://api.gateio.ws/api/v4
        config = Configuration(
            key=self.run_config.api_key, secret=self.run_config.api_secret, host=self.run_config.host_used)

        spot_api = SpotApi(ApiClient(config))
        try:
            # List all currency pairs supported
            api_response = spot_api.list_currency_pairs()
            print(api_response)
        except GateApiException as ex:
            print("Gate api exception, label: %s, message: %s\n" %
                (ex.label, ex.message))
        except ApiException as e:
            print("Exception when calling SpotApi->list_currency_pairs: %s\n" % e)


    # Get list ticker prices of  all currency pairs supported
    def list_tickers(self):
        # Initialize API client
        # Setting host is optional. It defaults to https://api.gateio.ws/api/v4
        config = Configuration(
            key=self.run_config.api_key, secret=self.run_config.api_secret, host=self.run_config.host_used)

        spot_api = SpotApi(ApiClient(config))
        try:
            # List all currency pairs supported
            api_response = spot_api.list_tickers()
            print(api_response)
        except GateApiException as ex:
            print("Gate api exception, label: %s, message: %s\n" %
                (ex.label, ex.message))
        except ApiException as e:
            print("Exception when calling SpotApi->list_currency_pairs: %s\n" % e)

    def get_pair(self, currency_pair):
        config = Configuration(
            key=self.run_config.api_key, secret=self.run_config.api_secret, host=self.run_config.host_used)

        spot_api = SpotApi(ApiClient(config))
        pair = spot_api.get_currency_pair(currency_pair)

        return pair

    def list_order_book(self, currency_pair):
        config = Configuration(
            key=self.run_config.api_key, secret=self.run_config.api_secret, host=self.run_config.host_used)

        spot_api = SpotApi(ApiClient(config))
        # str | Order depth. 0 means no aggregation is applied. default to 0 (optional) (default to '0')
        interval = '0'

        # int | Maximum number of order depth data in asks or bids (optional) (default to 10)
        limit = 10
        # bool | Return order book ID (optional) (default to False)
        with_id = False

        try:
            # Retrieve order book
            orderBook = spot_api.list_order_book(
                currency_pair, interval=interval, limit=limit, with_id=with_id)
            print(orderBook.asks[0][0])

            return orderBook
        except GateApiException as ex:
            print("Gate api exception, label: %s, message: %s\n" %
                (ex.label, ex.message))
        except ApiException as e:
            print("Exception when calling SpotApi->list_order_book: %s\n" % e)


    def list_orders(self, currency_pair):
        config = Configuration(
            key=self.run_config.api_key, secret=self.run_config.api_secret, host=self.run_config.host_used)

        spot_api = SpotApi(ApiClient(config))

        # int | Maximum number of order depth data in asks or bids (optional) (default to 10)
        limit = 10

        status = 'open'  # str | List orders based on status  `open` - order is waiting to be filled `finished` - order has been filled or cancelled
        page = 1  # int | Page number (optional) (default to 1)
        # int | Maximum number of records to be returned. If `status` is `open`, maximum of `limit` is 100 (optional) (default to 100)
        limit = 100
        # str | Specify operation account. Default to spot and margin account if not specified. Set to `cross_margin` to operate against margin account.  Portfolio margin account must set to `cross_margin` only (optional)
        account = 'spot'

        # int | Time range ending, default to current time (optional)
        to = 1635329650  # int(round(datetime.now().timestamp()))
        fromDate = datetime.now() - timedelta(days=1)
        from_ = 1627706330  # int(round(fromDate.timestamp()))
        # int | Start timestamp of the query (optional)
        # str | All bids or asks. Both included if not specified (optional)
        side = 'sell'

        print("To timestamp:" + str(to))
        print("From timestamp:" + str(from_))

        try:
            # List orders
            orders = spot_api.list_orders(currency_pair, status)

            print(orders)

            return orders
        except GateApiException as ex:
            print("Gate api exception, label: %s, message: %s\n" %
                (ex.label, ex.message))
        except ApiException as e:
            print("Exception when calling SpotApi->list_order_book: %s\n" % e)



if __name__ == '__main__':
    # init
    api_key = os.environ.get('gateio_api_key')
    api_secret = os.environ.get('gateio_secret_key')
    host_used = "https://api.gateio.ws/api/v4"

    # print(api_key)
    # print(api_secret)
    
    run_config = RunConfig(api_key, api_secret, host_used)
    gate_order = GateOrder(run_config)

    loop = asyncio.get_event_loop()

    loop.create_task(gate_order.create_order())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        #  screen.close()
        loop.close()