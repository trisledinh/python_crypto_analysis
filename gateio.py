import os
from datetime import datetime, timedelta
import logging
from decimal import Decimal as D

from gate_api import ApiClient, Configuration, Order, SpotApi, OrderBook
from gate_api.exceptions import ApiException, GateApiException

from config import RunConfig

logger = logging.getLogger(__name__)


def spot_demo(run_config):
    # type: (RunConfig) -> None
    currency_pair = "BTC_USDT"
    currency = currency_pair.split("_")[1]

    # Initialize API client
    # Setting host is optional. It defaults to https://api.gateio.ws/api/v4
    config = Configuration(key=run_config.api_key, secret=run_config.api_secret, host=run_config.host_used)
    spot_api = SpotApi(ApiClient(config))
    pair = spot_api.get_currency_pair(currency_pair)
    logger.info("testing against currency pair: " + currency_pair)
    min_amount = pair.min_base_amount

    # get last price
    tickers = spot_api.list_tickers(currency_pair=currency_pair)
    assert len(tickers) == 1
    last_price = tickers[0].last

    # make sure balance is enough
    order_amount = D(min_amount) * 2
    accounts = spot_api.list_spot_accounts(currency=currency)
    assert len(accounts) == 1
    available = D(accounts[0].available)
    logger.info("Account available: %s %s", str(available), currency)
    if available < order_amount:
        logger.error("Account balance not enough")
        return

    order = Order(amount=str(order_amount), price=last_price, side='buy', currency_pair=currency_pair)
    logger.info("place a spot %s order in %s with amount %s and price %s", order.side, order.currency_pair,
                order.amount, order.price)
    created = spot_api.create_order(order)
    logger.info("order created with id %s, status %s", created.id, created.status)
    if created.status == 'open':
        order_result = spot_api.get_order(created.id, currency_pair)
        logger.info("order %s filled %s, left: %s", order_result.id, order_result.filled_total, order_result.left)
        result = spot_api.cancel_order(order_result.id, currency_pair)
        if result.status == 'cancelled':
            logger.info("order %s cancelled", result.id)
    else:
        trades = spot_api.list_my_trades(currency_pair, order_id=created.id)
        assert len(trades) > 0
        for t in trades:
            logger.info("order %s filled %s with price %s", t.order_id, t.amount, t.price)

# Get list currency supported by GateIO


def get_list_currency(run_config):
    # Initialize API client
    # Setting host is optional. It defaults to https://api.gateio.ws/api/v4
    config = Configuration(
        key=run_config.api_key, secret=run_config.api_secret, host=run_config.host_used)

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
def list_tickers(run_config):
    # Initialize API client
    # Setting host is optional. It defaults to https://api.gateio.ws/api/v4
    config = Configuration(
        key=run_config.api_key, secret=run_config.api_secret, host=run_config.host_used)

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


def list_order_book(run_config, currency_pair):
    config = Configuration(
        key=run_config.api_key, secret=run_config.api_secret, host=run_config.host_used)

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


def list_orders(run_config, currency_pair):
    config = Configuration(
        key=run_config.api_key, secret=run_config.api_secret, host=run_config.host_used)

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
    to = 1635329650    #int(round(datetime.now().timestamp()))
    fromDate = datetime.now() - timedelta(days=1)
    from_ = 1627706330 #int(round(fromDate.timestamp()))
    # int | Start timestamp of the query (optional)
    # str | All bids or asks. Both included if not specified (optional)
    side = 'sell'

    print("To timestamp:" + str(to))
    print("From timestamp:" + str(from_))

    try:
        # List orders
        #orders = spot_api.list_all_open_orders(page=page, limit=limit, account=account)

        orders = spot_api.list_orders(currency_pair, status)

        #orders = spot_api.list_orders(currency_pair, status, page=page, limit=limit, account=account, _from=_from, to=to, side=side)

        print(orders)

        return orders
    except GateApiException as ex:
        print("Gate api exception, label: %s, message: %s\n" %
              (ex.label, ex.message))
    except ApiException as e:
        print("Exception when calling SpotApi->list_order_book: %s\n" % e)

def create_order(run_config):
    config = Configuration(
        key=run_config.api_key, secret=run_config.api_secret, host=run_config.host_used)

    spot_api = SpotApi(ApiClient(config))
    order = Order(currency_pair='BTC_USDT', side='buy', amount=0.001, price=16594) # Order | 

    print(order)    
    try:
        # List orders
        #orders = spot_api.list_all_open_orders(page=page, limit=limit, account=account)

        # Create an order
        orderResult = spot_api.create_order(order)
        print(orderResult)

        return order
    except GateApiException as ex:
        print("Gate api exception, label: %s, message: %s\n" %
              (ex.label, ex.message))
    except ApiException as e:
        print("Exception when calling SpotApi->list_order_book: %s\n" % e)


# init
api_key = os.environ.get('gateio_api_key')
api_secret = os.environ.get('gateio_secret_key')
host_used = "https://api.gateio.ws/api/v4"

# print(api_key)
# print(api_secret)
run_config = RunConfig(api_key, api_secret, host_used)

create_order(run_config)
