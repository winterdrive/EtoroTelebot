# https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments
import requests as req
import json
import redis
import os

# 簡易結構(詳細結構參考"20221105etoroTickers.txt")
# myJson={"InstrumentDisplayDatas": [
#   {
#     "InstrumentID": 100342,
#     "InstrumentDisplayName": "CryptoOps55",
#     "InstrumentTypeID": 10,
#     "ExchangeID": 8,
#     "Images": [
#       {
#         "InstrumentID": 100342,
#         "Width": 35,
#         "Height": 35,
#         "Uri": "https://etoro-cdn.etorostatic.com/market-avatars/100342/35x35.png"
#       },
#       {
#         "InstrumentID": 100342,
#         "Width": 50,
#         "Height": 50,
#         "Uri": "https://etoro-cdn.etorostatic.com/market-avatars/100342/50x50.png"
#       },
#       {
#         "InstrumentID": 100342,
#         "Width": 150,
#         "Height": 150,
#         "Uri": "https://etoro-cdn.etorostatic.com/market-avatars/100342/150x150.png"
#       }
#     ],
#     "SymbolFull": "CryptoOps55",
#     "InstrumentTypeSubCategoryID": 1001,
#     "PriceSource": "eToro",
#     "HasExpirationDate": false,
#     "IsInternalInstrument": true
#   },
#   {
#     "InstrumentID": 100342,
#     "InstrumentDisplayName": "CryptoOps55",
#     "InstrumentTypeID": 10,
#     "ExchangeID": 8,
#     "Images": [
#       {
#         "InstrumentID": 100342,
#         "Width": 35,
#         "Height": 35,
#         "Uri": "https://etoro-cdn.etorostatic.com/market-avatars/100342/35x35.png"
#       },
#       {
#         "InstrumentID": 100342,
#         "Width": 50,
#         "Height": 50,
#         "Uri": "https://etoro-cdn.etorostatic.com/market-avatars/100342/50x50.png"
#       },
#       {
#         "InstrumentID": 100342,
#         "Width": 150,
#         "Height": 150,
#         "Uri": "https://etoro-cdn.etorostatic.com/market-avatars/100342/150x150.png"
#       }
#     ],
#     "SymbolFull": "CryptoOps55",
#     "InstrumentTypeSubCategoryID": 1001,
#     "PriceSource": "eToro",
#     "HasExpirationDate": false,
#     "IsInternalInstrument": true
#   }
# ]
# }

# app.config['REDIS_HOST']=os.getenv('REDIS_HOST')
# app.config['REDIS_PORT']=os.getenv('REDIS_PORT')
# app.config['REDIS_PASSWORD']=os.getenv('REDIS_PASSWORD')
# conn = redisService.get_redis_connection(app.config['REDIS_HOST'], app.config['REDIS_PORT'], app.config['REDIS_PASSWORD'])

ETORO_DICT_KEY_NAME = "etoroDict"
ETORO_WATCHLIST_TODAY_KEY_NAME = "etoroWatchListToday"


class Redis(object):
    """
    redis 數據操作
    """

    @staticmethod
    def get_redis_connection():
        return redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'),
                           password=os.getenv('REDIS_PASSWORD'), charset="utf-8", decode_responses=True)

    @classmethod
    def initialize_state_of_num_and_ticker_pairs_in_redis(cls):
        conn = cls.get_redis_connection()
        resp = req.get("https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments")
        data = resp.text
        myJsonList = json.loads(data)["InstrumentDisplayDatas"]
        myEtoroList = list()
        for i in myJsonList:
            # print(i["InstrumentID"])
            # print(i["SymbolFull"])
            myEtoroList.append(",".join([str(i["InstrumentID"]), str(i["SymbolFull"]).replace('.', '_')]))
        # print(len(myEtoroList))
        # print(myEtoroList[0])
        myRedisScoreDict = dict()
        for i in myEtoroList:
            myRedisScoreDict[i] = 111
        conn.zadd(ETORO_DICT_KEY_NAME, myRedisScoreDict)
        # 最終結構是etoroDict(zset)內有4845條類似111:1,EURUSD的結構
        print('reset redis by job')
        return

    @classmethod
    def change_state_of_num_and_ticker_pairs_in_redis_when_finish(cls, member: str):
        conn = cls.get_redis_connection()
        conn.zadd(ETORO_DICT_KEY_NAME, {member: 999})
        return


    @classmethod
    def change_state_of_num_and_ticker_pairs_in_redis_when_finish_in_lua(cls):#快又穩，又保證原子性
        conn = cls.get_redis_connection()
        script="""
        local key = KEYS[1]
        local upper = ARGV[1]
        local lower = ARGV[2]
        local value = ARGV[3]
        local myList = redis.call('ZRANGEBYSCORE',key,lower,upper,'LIMIT', 0, 100)  
        for i,v in pairs(myList) do
            redis.call('ZADD',key,value,v)  
        end 
        return myList
        """
        key = ETORO_DICT_KEY_NAME
        upper=120
        lower=100
        value = 999
        cmd = conn.register_script(script)
        my_count=0
        # 取值的也放lua裡面，return出來即可。「取值-->改狀態」，一氣呵成
        result=cmd(keys=[key],args=[upper,lower,value])
        return result


    @classmethod
    def get_member_in_initial_state(cls, keyName: str):
        conn = cls.get_redis_connection()
        myList = conn.zrangebyscore(keyName, '100', '120', start=0, num=100)
        return myList

    @classmethod
    def get_member_in_finish_state(cls, keyName: str):
        conn = cls.get_redis_connection()
        myList = conn.zrangebyscore(keyName, '888', '1000', start=0, num=100)
        return myList

    @classmethod
    def add_watchListToday_in_redis(cls, tickerList):
        conn = cls.get_redis_connection()
        # conn.sadd(ETORO_WATCHLIST_TODAY_KEY_NAME, 'null')
        for i in tickerList:
            conn.sadd(ETORO_WATCHLIST_TODAY_KEY_NAME, i)
        # print('member added')
        return

    @classmethod
    def get_watchListToday_in_redis(cls):
        conn = cls.get_redis_connection()
        myList = conn.smembers(ETORO_WATCHLIST_TODAY_KEY_NAME)
        # print('member get')
        return myList

    @classmethod
    def delete_watchListToday_element_in_redis(cls, ticker_name):
        conn = cls.get_redis_connection()
        # 刪到空會整個key不見
        myList = conn.srem(ETORO_WATCHLIST_TODAY_KEY_NAME, ticker_name)
        # print('member get')
        return myList
