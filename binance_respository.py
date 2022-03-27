import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import talib
import seaborn as sns

from pandas import read_csv, set_option
from pandas.plotting import scatter_matrix
from pymongo import MongoClient

import os
from datetime import datetime
from binance.client import Client

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# init
api_key = os.environ.get('binance_api_key')
api_secret = os.environ.get('binance_secret_key')

def get_klines_data(assetName, interval):
    client = Client(api_key, api_secret)
    # valid intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M

    df_last_kline = get_last_kline_candle(assetName, interval, "BNM")
    
    timestamp = 0
    
    #print(df_last_kline)
    if df_last_kline.empty:
        # get timestamp of earliest date data is available
        timestamp = client._get_earliest_valid_timestamp(assetName, interval)
        #print(timestamp)
    else:
        timestamp = df_last_kline["OpenTime"][0]
        
        del_query = {"OpenTime": {'$gte': timestamp}, "AssetName" : assetName, "Period": interval}
        
        delete_many("KlineCandles", del_query)
        
        timestamp = timestamp.strftime("%Y-%m-%d")
        print(timestamp)

    
    bars = client.get_historical_klines(assetName, interval, timestamp)
    
    klines = convert_klines_to_dict(bars, assetName, interval, "BNM")
    
        
    #Insert Kline Collection
    insert_klines_data(klines)
    
    #Update or Insert Last Kline
    last_kline = klines[-1]
    
      
    
    update_last_kline_candle(last_kline)

    return klines

def connect_mongodb(host, port, username, password, dbName):
    """ A util for making a connection to mongo """

    if username and password:
        mongo_uri = 'mongodb://%s:%s@%s:%s/%s' % (username, password, host, port, dbName)
        conn = MongoClient(mongo_uri)
    else:
        conn = MongoClient(host, port)


    return conn[dbName]


def read_collection(db, collection, query={}):
    """ Read from Mongo and Store into DataFrame """
    "Default: localhost, port: 27018"
    # Connect to MongoDB
    #db = _connect_mongo(host=host, port=port, username=username, password=password, db=db)

    # Make a query to the specific DB and Collection
    cursor = db[collection].find(query)

    # Expand the cursor and construct the DataFrame
    df =  pd.DataFrame(list(cursor))

    return df

def delete_one(collection, query={}):
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    #query = {"Name": { "$regex": 'USDT$' }}
    mycol  = db[collection]
    x = mycol.delete_one(query)
    
    return x

def delete_many(collection, query={}):
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    #query = {"Name": { "$regex": 'USDT$' }}
    mycol  = db[collection]
    x = mycol.delete_many(query)
    
    return x

def read_candles(period, assetName):
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    df = read_collection(db, "TradeCandles", {"Period": period, "AssetName": assetName})

    df = df.loc[:, ["OpenTime", "CloseTime", "AssetName", "Period", "HighPrice", "LowPrice", "OpenPrice", "ClosePrice", "Volume", "NumberTrades"]]
    df["HighPrice"] = df["HighPrice"].astype('float')
    df["LowPrice"] = df["LowPrice"].astype('float')
    df["OpenPrice"] = df["OpenPrice"].astype('float')
    df["ClosePrice"] = df["ClosePrice"].astype('float')


    df["BienDo"] = df["HighPrice"] - df["LowPrice"]
    df["%BienDo"] = df["BienDo"]/df["ClosePrice"]*100

    df["OpenTime"] = pd.to_datetime(df['OpenTime']) + pd.DateOffset(hours=7)
    df["CloseTime"] = pd.to_datetime(df['CloseTime']) + pd.DateOffset(hours=7)

    df["OpenTime"] = pd.to_datetime(df['OpenTime'], format='%Y-%m-%d')
    df["CloseTime"] = pd.to_datetime(df['OpenTime'], format='%Y-%m-%d')
    
    df.rename(columns={"ClosePrice": "Close", "HighPrice": "High", "LowPrice": "Low", "OpenPrice": "Open"}, inplace=True)
    
    return df

def query_kline_candles(query):
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    df = read_collection(db, "KlineCandles",query)
    
    df = df.loc[:, ["OpenTime", "CloseTime", "AssetName", "Period", "High", "Low", "Open", "Close", "Volume", "QuoteVolume", "NumberTrades"]]
    df["High"] = df["High"].astype('float')
    df["Low"] = df["Low"].astype('float')
    df["Open"] = df["Open"].astype('float')
    df["Close"] = df["Close"].astype('float')
    df["Volume"] = df["Volume"].astype('float')
    df["QuoteVolume"] = df["QuoteVolume"].astype('float')

    df["BienDo"] = df["High"] - df["Low"]
    df["%BienDo"] = df["BienDo"]/df["Close"]*100

    df["OpenTime"] = pd.to_datetime(df['OpenTime']) - pd.DateOffset(hours=7) #pd.to_datetime(df['OpenTime'], format='%d-%m-%Y')
    df["CloseTime"] = pd.to_datetime(df['CloseTime']) - pd.DateOffset(hours=7) #pd.to_datetime(df['CloseTime'], format='%d-%m-%Y')
    
    return df

def read_assets():
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    query = {"Name": { "$regex": 'USDT$' }, "IsListing": 1}
    df = read_collection(db, "TradeAssets", query)
    return df

def insert_ana_asset(ana):
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    anaCollection = db["AnaAssets"]

    #mydict = { "AssetName": "BTCUSDT", "Period": "Daily", "BullishTypeOfTwoCanldes": "TwoDown", "RateOfPull": 10.1, "RateOfDown": 9.1, "RateOfSideway": 10 }

    x = anaCollection.insert_one(ana)

    return x

def read_kline_candles(assetName, period):
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    df = read_collection(db, "KlineCandles", {"Period": period, "AssetName": assetName})
    
    df = df.loc[:, ["OpenTime", "CloseTime", "AssetName", "Period", "High", "Low", "Open", "Close", "Volume", "NumberTrades"]]
    df["High"] = df["High"].astype('float')
    df["Low"] = df["Low"].astype('float')
    df["Open"] = df["Open"].astype('float')
    df["Close"] = df["Close"].astype('float')
    df["Volume"] = df["Volume"].astype('float')


    df["BienDo"] = df["High"] - df["Low"]
    df["%BienDo"] = df["BienDo"]/df["Close"]*100

    #df["OpenTime"] = pd.to_datetime(df['OpenTime']) + pd.DateOffset(hours=7)
    #df["CloseTime"] = pd.to_datetime(df['CloseTime']) + pd.DateOffset(hours=7)

    #df["OpenTime"] = pd.to_datetime(df['OpenTime'], format='%Y-%m-%d')
    #df["CloseTime"] = pd.to_datetime(df['OpenTime'], format='%Y-%m-%d')
    
    return df
    
def insert_klines_data(klines):
    #klines is array of dictionary:
    
    #mydict = { "AssetName": "BTCUSDT", "Period": "Daily", "OpenTimeLong": 1502928000000, /
    #"Open": 1.0, "Close": 10.1, "High": 11.1, "Low": 8, "Volume": 99999, "CloseTimeLong": 1602928000000, /
    #"QuoteVolume": 1818181, "NumberTrades": 919191, "TakerBaseVolume": 91919,"TakerQuoteVolume": 9999, "Ignore":818181,
    #"OpenTime": Datetime, "CloseTime": DateTime, "MarketExchangeId": MarketExchangeId, "MarketExchangeCode" : "BNM" }
    
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    klineCollection = db["KlineCandles"]
    
    x = klineCollection.insert_many(klines)
    return x.inserted_ids

def convert_klines_to_dict(list_klines, assetName, period, marketExchangeCode):
    klines = []
    
    for row in list_klines:
        mydict = {
            "AssetName": assetName, "Period": period, "OpenTimeLong": row[0], 
            "Open": row[1], "High": row[2], "Low": row[3], "Close": row[4], "Volume": row[5], "CloseTimeLong": row[6], 
            "QuoteVolume": row[7], "NumberTrades": row[8], "TakerBaseVolume": row[9],"TakerQuoteVolume": row[10], "Ignore":row[11],
            "OpenTime": convert_longtime_date(row[0]), "CloseTime": convert_longtime_date(row[6]), "MarketExchangeCode" : marketExchangeCode
        }
        
        klines.append(mydict)
        
    return klines
        
def convert_longtime_date(timestamp):
    if timestamp > 10**12:
        timestamp = timestamp/1000
        
    return datetime.fromtimestamp(timestamp)

def get_listing_coins():
    client = Client(api_key, api_secret)
    info = client.get_all_tickers()
    
    return info

def update_coins_listing():
    
    #reset all listing = 0
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    tradAsset = db["TradeAssets"]
    query = {}
    newvalues = { "$set": {'IsListing': 0} }
    tradAsset.update_many(query, newvalues)
    
    #update listing coins
    lst = get_listing_coins()
    
    symbols = []
    for i in lst:
        symbols.append(i["symbol"])
    
    print(symbols)
    query = {"Name": {"$in": symbols}}
    
    newvalues = { "$set": {'IsListing': 1} }
    
    x = tradAsset.update_many(query, newvalues)

    return x

def get_bnb_marketinfo():
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    df = read_collection(db, "MarketExchanges", {"Code": "BNM"})
    return df.head(1)

def update_last_kline_candle(last_kline):
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    
    lastKCollection = db["LastKlineCandles"]
    
    #print(last_kline["AssetName"])
    
    newvalues = { "$set": {'OpenTimeLong': last_kline["OpenTimeLong"], "Open": last_kline["Open"], "High": last_kline["High"],
                                 "Low": last_kline["Low"], "Close": last_kline["Close"], "Volume": last_kline["Volume"], 
                                 "CloseTimeLong": last_kline["CloseTimeLong"], "QuoteVolume": last_kline["QuoteVolume"], 
                                 "NumberTrades": last_kline["NumberTrades"], "TakerBaseVolume": last_kline["TakerBaseVolume"],
                                 "TakerQuoteVolume": last_kline["TakerQuoteVolume"], "Ignore":last_kline["Ignore"], 
                                "OpenTime": last_kline["OpenTime"], "CloseTime": last_kline["CloseTime"]
                                } }
    
    x = lastKCollection.update_one({'AssetName': last_kline["AssetName"], "Period": last_kline["Period"], "MarketExchangeCode": last_kline["MarketExchangeCode"]},
                               newvalues, upsert=True)

    return x

def get_last_kline_candle(assetName, period, marketExchangeCode):
    db = connect_mongodb("localhost", 27018, "", "", "trady")
    lastKCollection = db["LastKlineCandles"]

    cursor = lastKCollection.find({"AssetName": assetName, "Period": period, "MarketExchangeCode": marketExchangeCode})
    
    #print(cursor)
    if (cursor != None):
        df =  pd.DataFrame(list(cursor))
        return df
    return None

def sync_data(period):
    df_assets = read_assets()
    
    #print(df_assets)
    for i, row in df_assets.iterrows():
        assetName = row["Name"]
        print(assetName)
        get_klines_data(assetName, period)
        print(assetName + " has been synced!")

def ana_candle_patern(df):
    df["CandlePatern"] = np.nan
    df["NextBullishType"] = np.nan

    MINIMUM_MIDDLE_RANGE = 0.1
    #MINIMUM_SP_RANGE = 0.4
    
    UP_RANGE = 1/3
    DOWN_RANGE = 2/3
    
    UP_DB_RANGE = 1/5
    DOWN_DB_RANGE = 4/5
    
    length_df = len(df)

    for index, row in df.iterrows():
        op = row["Open"]
        cp = row["Close"]
        hp = row["High"]
        lp = row["Low"]
        tr = row["BienDo"]
        tr_oc = abs(cp - op)
        
        if tr == 0: continue

        middle_oc = (op + cp)/2
        tr_middle = abs(hp - middle_oc)
        
        if (tr_middle/tr < UP_RANGE):
            #UP
            if (tr_middle/tr < UP_DB_RANGE):
                patern = "UP_DAC_BIET"
            else:
                patern = "UP"
        elif (tr_middle/tr > DOWN_RANGE):
            #DOWN
            if (tr_middle/tr > DOWN_DB_RANGE):
                patern = "DOWN_DAC_BIET"
            else:
                patern = "DOWN"
        elif (tr_oc/tr>= 0.8):
            patern = "MIDDLE_FULL"
        elif (tr_oc/tr<= 0.02):
            patern = "MIDDLE_DOJI"
        else:
            #Cây Middle 
            patern = "MIDDLE"
            
        df.loc[index, 'CandlePatern'] = patern        

        #Bien dong tang hay giam
        if(cp>op):
            df.loc[index, 'BienDong'] = 1 
        elif(cp<op):
            df.loc[index, 'BienDong'] = -1
        else:
            df.loc[index, 'BienDong'] = 0

        #Cây sau là cây tăng giá hay giảm giá
        cp_next = 0
        if (index < length_df -1):
            cp_next = df.loc[index + 1, "Close"]

            if (abs(cp_next - cp)/tr <= MINIMUM_MIDDLE_RANGE):
                df.loc[index, 'NextBullishType'] = 0
            elif (cp_next > cp):
                df.loc[index, 'NextBullishType'] = 1
            else:
                df.loc[index, 'NextBullishType'] = -1       

def ana_twocandles(df):
    df["TwoCandlePatern"] = np.nan
    candle_paterns = ["DOWN", "UP", "UP_DAC_BIET", "DOWN_DAC_BIET", "MIDDLE", "MIDDLE_DOJI", "MIDDLE_FULL"]
    
    for index, row in df.iterrows():
                
        if (index == 0):
            continue
        
        for x1 in candle_paterns:
            for x2 in candle_paterns:
                if (df.loc[index, "CandlePatern"] == x1 and df.loc[index - 1, "CandlePatern"] == x2):
                    #df.loc[index, x1 + "@" + x2] = 1
                    df.loc[index, "TwoCandlePatern"] = x1 + "@" + x2
                    
def ana_pct_change(df):
    df['PriceChange'] = df["Close"].pct_change().fillna(0)
    df["MFI14"] = talib.MFI(df["High"], df["Low"], df["Close"], df["Volume"], timeperiod=14)
    df["RSI14"] = talib.RSI(df["Close"], 14)
    df["MA10"] = talib.MA(df["Close"], 10)
    df["MA20"] = talib.MA(df["Close"], 20)
    df["MA50"] = talib.MA(df["Close"], 50)
    
    bins = [0, 4, 7, 10, 13, np.inf]
    names = ['<4', '4-7', '7-10', '10-13', '13+']

    df["%BienDo_Bins"] = pd.cut(df['%BienDo'], bins=bins, labels=names)
    
    #Price
    df["%PRICE_CHANGE_1D"] = df["Close"].pct_change()*100.0
    df["%PRICE_CHANGE_2D"] = df["Close"].pct_change(periods=2)*100.0
    df["%PRICE_CHANGE_3D"] = df["Close"].pct_change(periods=3)*100.0
    df["%PRICE_CHANGE_7D"] = df["Close"].pct_change(periods=7)*100
    df["%PRICE_CHANGE_2W"] = df["Close"].pct_change(periods=14)*100.0
    df["%PRICE_CHANGE_3W"] = df["Close"].pct_change(periods=21)*100.0
    df["%PRICE_CHANGE_4W"] = df["Close"].pct_change(periods=28)*100.0
    df["%PRICE_CHANGE_8W"] = df["Close"].pct_change(periods=56)*100.0
    df["%PRICE_CHANGE_12W"] = df["Close"].pct_change(periods=84)*100.0
    df["%PRICE_CHANGE_24W"] = df["Close"].pct_change(periods=168)*100.0
    df["%PRICE_CHANGE_52W"] = df["Close"].pct_change(periods=364)*100.0
    #Volume
    df["%VOLUME_CHANGE_1D"] = df["Volume"].pct_change()*100.0
    df["%VOLUME_CHANGE_2D"] = df["Volume"].pct_change(periods=2)*100.0
    df["%VOLUME_CHANGE_3D"] = df["Volume"].pct_change(periods=3)*100.0
    df["%VOLUME_CHANGE_7D"] = df["Volume"].pct_change(periods=7)*100.0
    df["%VOLUME_CHANGE_2W"] = df["Volume"].pct_change(periods=14)*100.0
    df["%VOLUME_CHANGE_3W"] = df["Volume"].pct_change(periods=21)*100.0
    df["%VOLUME_CHANGE_4W"] = df["Volume"].pct_change(periods=28)*100.0
    df["%VOLUME_CHANGE_8W"] = df["Volume"].pct_change(periods=56)*100.0
    df["%VOLUME_CHANGE_12W"] = df["Volume"].pct_change(periods=84)*100.0
    df["%VOLUME_CHANGE_24W"] = df["Volume"].pct_change(periods=168)*100.0
    df["%VOLUME_CHANGE_52W"] = df["Volume"].pct_change(periods=364)*100.0
    
    df["%NUMBER_TRADES_CHANGE_1D"] = df["NumberTrades"].pct_change()*100.0

def ana_candle_next_partern(df): 
    df["NextCandlePatern"] = np.nan 
    df["BreakHighPrice"] = np.nan
    df["BreakLowPrice"] = np.nan
    
    length_df = df.shape[0]

    for i in range(0,length_df-1):
        df.loc[i, "NextCandlePatern"] = df.loc[i+1, "CandlePatern"]
        df.loc[i, "BreakHighPrice"] = df.loc[i+1, "High"] > df.loc[i, "High"]
        df.loc[i, "BreakLowPrice"] = df.loc[i+1, "Low"] < df.loc[i, "Low"]
        df.loc[i, "Inside"] = df.loc[i+1, "High"] <= df.loc[i, "High"] and df.loc[i+1, "Low"] >= df.loc[i, "Low"]
    
def normalize_data(df):
    df["BreakHighPrice"] = df["BreakHighPrice"].astype('float')
    df["BreakLowPrice"] = df["BreakLowPrice"].astype('float')
    df["Inside"] = df["Inside"].astype('float')
    df["Volume"] = df["Volume"].astype("float")
    
    #df["CandlePatern"].replace(['MIDDLE', 'UP', 'UP_DAC_BIET' , 'DOWN', 'DOWN_DAC_BIET', 'MIDDLE_FULL', 'MIDDLE_DOJI'],
    #                    [0, 1, 2, 3, 4, 5, 6], inplace=True)
    
    #df["NextCandlePatern"].replace(['MIDDLE', 'UP', 'UP_DAC_BIET' , 'DOWN', 'DOWN_DAC_BIET', 'MIDDLE_FULL', 'MIDDLE_DOJI'],
    #                    [0, 1, 2, 3, 4, 5, 6], inplace=True)
    
    df["TwoCandlePatern_"] = pd.factorize(df['TwoCandlePatern'])[0]
    df["%BienDo_Bins"] = pd.factorize(df['%BienDo_Bins'])[0]
    #df["BreakHighPrice_"] = pd.factorize(df['BreakHighPrice'])[0]

def ana_two_candle(df, patern):
    if patern in df.columns:
        df2 = df[df[patern] == 1].groupby("NextCandlePatern")
        df3 = pd.DataFrame({"TwoCandlePatern": patern,"Count":df2.size()})
        df3.reset_index(inplace=True)
        df3.set_index('TwoCandlePatern', inplace=True)
        df3["Percent"] = (df3["Count"]/df3["Count"].sum())*100
        return df3    
def ana_two_candles(paterns):
    datas = map (ana_two_candle, paterns)
    return(pd.concat(datas, names=['TwoCandlePatern']))

#Get all records with period and analysis data to data frame
def get_all_df(period):
      
    query = {"Period": period}
    df = query_kline_candles(query)

    #Get All assets
    df_assets = read_assets()
    symbols = df_assets["Name"].array

    #Construct Empty Data Frame
    all_df = pd.DataFrame()

    for s in symbols:
        df1= df[df["AssetName"] == s].copy()
        df1.reset_index(inplace=True)

        ana_candle_patern(df1)
        ana_pct_change(df1)

        all_df = pd.concat([all_df, df1], axis = 0)    
        
    return all_df

# Get candle patern of date: format date: %Y-%m-%d
def get_candle_type(symbol, date, all_df):
    
    df = all_df[(all_df["AssetName"] == symbol) & (all_df["OpenTime"] >= date)]

    #print(df.tail(10))
    candle_patern = df["CandlePatern"].iloc[0]
    
    return candle_patern

#top change price or volume: from_date is string at format yyyy-mm-dd
def get_recent_top_vol_change(from_date, all_df):

    df = all_df[(all_df["OpenTime"] >= from_date) & ((all_df["%VOLUME_CHANGE_1D"] >= 300) | (all_df["%NUMBER_TRADES_CHANGE_1D"] >= 300))]
    df = df.sort_values(by=['OpenTime'], ascending=False).head(20).loc[:, ["AssetName", "OpenTime", "Close", "%VOLUME_CHANGE_1D", "%PRICE_CHANGE_1D", "%PRICE_CHANGE_2D", "%PRICE_CHANGE_7D", "%VOLUME_CHANGE_7D", "%NUMBER_TRADES_CHANGE_1D", "Volume",  "CandlePatern", "RSI14", "MFI14"]]

    return df

def get_recent_top_price_change(from_date, all_df):

    df = all_df[(all_df["OpenTime"] >= from_date) & ((all_df["%PRICE_CHANGE_1D"] >= 15))]
    df = df.sort_values(by=['OpenTime'], ascending=False).head(20).loc[:, ["AssetName", "OpenTime", "Close", "%VOLUME_CHANGE_1D", "%PRICE_CHANGE_1D", "%PRICE_CHANGE_2D", "%PRICE_CHANGE_7D", "%VOLUME_CHANGE_7D", "%NUMBER_TRADES_CHANGE_1D", "Volume",  "CandlePatern", "RSI14", "MFI14"]]

    return df

def get_buy_signal_mfi(from_date, all_df):

    df = all_df[(all_df["OpenTime"] >= from_date) & (all_df["MFI14"] <= 25) & (all_df["RSI14"] <= 30)]
    df = df.sort_values(by=['OpenTime'], ascending=False).head(20).loc[:, ["AssetName", "OpenTime", "Close", "%VOLUME_CHANGE_1D", "%PRICE_CHANGE_1D", "%PRICE_CHANGE_2D", "%PRICE_CHANGE_7D", "%VOLUME_CHANGE_7D", "%NUMBER_TRADES_CHANGE_1D", "Volume",  "CandlePatern", "RSI14", "MFI14"]]

    return df

def get_sell_signal_mfi(from_date, all_df):

    df = all_df[(all_df["OpenTime"] >= from_date) & (all_df["MFI14"] >= 80) & (all_df["RSI14"] >= 70) ]
    df = df.sort_values(by=['OpenTime'], ascending=False).head(20).loc[:, ["AssetName", "OpenTime", "Close", "%VOLUME_CHANGE_1D", "%PRICE_CHANGE_1D", "%PRICE_CHANGE_2D", "%PRICE_CHANGE_7D", "%VOLUME_CHANGE_7D", "%NUMBER_TRADES_CHANGE_1D", "Volume",  "CandlePatern", "RSI14", "MFI14"]]

    return df