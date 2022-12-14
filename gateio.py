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
        
        config = Configuration(
                key=self.run_config.api_key, secret=self.run_config.api_secret, host=self.run_config.host_used)

        self.spot_api = SpotApi(ApiClient(config))
        self.run_config = run_config
        self.db = DBManager("localhost", 27018, "", "", "trady")
        self.order_ids = []

    async def create_order(self):
        
        while True:
            await asyncio.sleep(5)
            
            query = {"Type": "buy", "Status": "0"}

            order_wait = self.db.read_one("OrderBook", query)

            if order_wait is not None:

                print(order_wait["Pair"])
                ask_pair = order_wait["Pair"]
                ask_side = order_wait["Type"]
                ask_amount = D(order_wait["Amount"])
                ask_price = D(order_wait["Price"])

                # self.update_order_status(db, "0")

                order = Order(currency_pair=ask_pair, side=ask_side,
                            amount=ask_amount, price=ask_price)  # Order |

                currency = ask_pair.split("_")[1]
                try:
                    accounts = self.spot_api.list_spot_accounts(currency=currency)
                    assert len(accounts) == 1
                    available = D(accounts[0].available)
                    logger.info("Account available: %s %s", str(available), currency)
                    if available < ask_amount:
                        logger.error("Account balance not enough")
                        return
                    # Create an order
                    orderResult = self.spot_api.create_order(order)
                    print(orderResult)
                    logger.info("order created with id %s, status %s",
                            orderResult.id, orderResult.status)

                    if orderResult.status == 'open':
                        self.order_ids.append({"Id": orderResult.id, "Status": orderResult.status, "Pair": ask_pair})

                        self.update_order_id(order_wait._id, orderResult.id)

                        order_result = self.spot_api.get_order(orderResult.id, ask_pair)
                        logger.info("order %s filled %s, left: %s", order_result.id,
                                    order_result.filled_total, order_result.left)
                        result = self.spot_api.cancel_order(order_result.id, ask_pair)
                        if result.status == 'cancelled':
                            logger.info("order %s cancelled", result.id)
                    else:
                        trades = self.spot_api.list_my_trades(ask_pair, order_id=orderResult.id)
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

    async def check_order_status(self):
        while True:
            await asyncio.sleep(1)
            
            try:

                query = {"Type": "buy", "Status": "1"}
                # ord = self.db.read_one("OrderBook", query)

                for ord in self.order_ids:
                    ord_result = self.spot_api.get_order(ord.id, ord.Pair)

                    logger.info("order %s filled %s, left: %s", ord_result.id,
                                            ord_result.filled_total, ord_result.left)
                    
                    if (ord_result.left == 0):
                        self.update_order_status(ord.id, "2")
            except GateApiException as ex:
                print("Gate api exception, label: %s, message: %s\n" %
                        (ex.label, ex.message))
                break
            except ApiException as e:
                print("Exception when calling SpotApi->list_order_book: %s\n" % e)
                break
            except Exception as e:
                print("Exception when calling SpotApi->list_order_book: %s\n" % e)
                break

    def update_order_status(self, ord_id, new_status):
        filter = {"Type": "buy", "OrderId": ord_id}

                # Values to be updated.
        newvalues = { "$set": { 'Status': new_status } }
        self.db.update_one("OrderBook", filter, newvalues)

    def update_order_id(self, id, ord_id):
        filter = {"Type": "buy", "_id": id}

                # Values to be updated.
        newvalues = { "$set": { 'OrderId': ord_id, 'Status': "1" } }
        self.db.update_one("OrderBook", filter, newvalues)

    # Get list currency supported by GateIO
    def get_list_currency(self):
        try:
            # List all currency pairs supported
            api_response = self.spot_api.list_currency_pairs()
            print(api_response)
        except GateApiException as ex:
            print("Gate api exception, label: %s, message: %s\n" %
                (ex.label, ex.message))
        except ApiException as e:
            print("Exception when calling SpotApi->list_currency_pairs: %s\n" % e)


    # Get list ticker prices of  all currency pairs supported
    def list_tickers(self):
        try:
            # List all currency pairs supported
            api_response = self.spot_api.list_tickers()
            print(api_response)
        except GateApiException as ex:
            print("Gate api exception, label: %s, message: %s\n" %
                (ex.label, ex.message))
        except ApiException as e:
            print("Exception when calling SpotApi->list_currency_pairs: %s\n" % e)

    def get_pair(self, currency_pair):
        pair = self.spot_api.get_currency_pair(currency_pair)

        return pair

    def list_orders(self, currency_pair):
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
            orders = self.spot_api.list_orders(currency_pair, status)

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
    loop.create_task(gate_order.check_order_status())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        #  screen.close()
        loop.close()