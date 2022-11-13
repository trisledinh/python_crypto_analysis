import os
from datetime import datetime
import logging
from decimal import Decimal as D

from gate_api import ApiClient, Configuration, Order, SpotApi
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

    print(config.host)

    spot_api = SpotApi(ApiClient(config))
    pair = spot_api.get_currency_pair(currency_pair)
    logger.info("testing against currency pair: " + currency_pair)
    min_amount = pair.min_base_amount

    # get last price
    tickers = spot_api.list_tickers(currency_pair=currency_pair)
    assert len(tickers) == 1
    last_price = tickers[0].last

    print(last_price)

def get_list_currency(run_config):
     # Initialize API client
    # Setting host is optional. It defaults to https://api.gateio.ws/api/v4
    config = Configuration(key=run_config.api_key, secret=run_config.api_secret, host=run_config.host_used)

    spot_api = SpotApi(ApiClient(config))
    try:
        # List all currency pairs supported
            api_response = spot_api.list_currency_pairs()
            print(api_response)
    except GateApiException as ex:
            print("Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message))
    except ApiException as e:
            print("Exception when calling SpotApi->list_currency_pairs: %s\n" % e)


def list_tickers(run_config):
     # Initialize API client
    # Setting host is optional. It defaults to https://api.gateio.ws/api/v4
    config = Configuration(key=run_config.api_key, secret=run_config.api_secret, host=run_config.host_used)

    spot_api = SpotApi(ApiClient(config))
    try:
        # List all currency pairs supported
            api_response = spot_api.list_tickers()
            print(api_response)
    except GateApiException as ex:
            print("Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message))
    except ApiException as e:
            print("Exception when calling SpotApi->list_currency_pairs: %s\n" % e)



# init
api_key = "94124f7b0d62ff172142a69703a41daa" #os.environ.get('gateio_api_key')
api_secret = "d63e4593776f9ee30749efcc79ce89c6ccf39b30904e101de6a9ca3d04f0c4ef" #os.environ.get('gateio_secret_key')
host_used = "https://api.gateio.ws/api/v4"

#print(api_key)
#print(api_secret)
run_config = RunConfig(api_key, api_secret, host_used)

list_tickers(run_config)