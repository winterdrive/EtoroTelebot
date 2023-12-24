# pip install pandas yfinance plotly

""" 
這裡要繪製的是market heatmap，因為要去yahoo finance取500筆資料，
所以我們一天存一次到Redis內，每次使用者訪問的時候去redis拿資料就好。
資料更新的部分，觸發點可以設計在每日job跟強制更新按鈕(按鈕前後端都要debounce)。
最後匯出成html檔即可。
"""
from dotenv import load_dotenv
import plotly.express as px
import pandas as pd
import yfinance as yf
import redis
import os
import pickle
import json
import redisService

""" redis連線 """
load_dotenv()
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')


def initialize_state_of_num_and_ticker_pairs_in_redis():
    redis = redisService.Redis.get_redis_connection()
    redis.zadd("ETORO_DICT_KEY_NAME", {"member": 999})
    # 最終結構是etoroDict(zset)內有4845條類似111:1,EURUSD的結構
    print('reset redis by job')
    return


""" 存資料到redis """


def save_yahoo_finance_sp500_data_to_redis():
    sp500 = pd.read_html(
        r'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol']

    tickers = []
    sectors = []
    deltas = []
    market_caps = []

    for ticker in sp500:
        # for ticker in ['MSFT','ABMD']:
        try:
            # 為確保資料處理具有原子性，所有資料處理完後都先存成變數，沒報錯才塞進list內

            # create Ticker object
            stock = yf.Ticker(ticker)
            # add print statement to ensure code is running
            append_element_tickers = ticker
            # download info
            info = stock.info
            # download sector
            append_element_sectors = info['sector']
            # download daily stock prices for 2 days
            hist = stock.history('2d')
            # calculate change in stock price (from a trading day ago)
            append_element_deltas = (hist['Close'][1] - hist['Close'][0]) / hist['Close'][0]
            # calculate market cap
            append_element_market_caps = info['sharesOutstanding'] * info['previousClose']

            tickers.append(append_element_tickers)
            sectors.append(append_element_sectors)
            deltas.append(append_element_deltas)
            market_caps.append(append_element_market_caps)

            print(f'downloaded {ticker}')

        except Exception as e:
            print(f'downloaded {ticker} failed')
            print(e)

    tickers_list = tickers
    sectors_list = sectors
    deltas_list = deltas
    market_caps_list = market_caps

    redis = redisService.Redis.get_redis_connection()
    pipe = redis.pipeline()
    pipe.delete("tickers")
    pipe.delete("sectors")
    pipe.delete("deltas")
    pipe.delete("market_caps")

    for i in range(0, len(tickers_list)):
        # print(tickers_list[i])
        pipe.rpush('tickers', tickers_list[i])
        pipe.rpush('sectors', sectors_list[i])
        pipe.rpush('deltas', deltas_list[i])
        pipe.rpush('market_caps', market_caps_list[i])
    pipe.execute()

    return tickers_list, sectors_list, deltas_list, market_caps_list


""" 取資料 """


def get_yahoo_finance_sp500_data_to_redis(renew: bool = False):
    redis = redisService.Redis.get_redis_connection()
    if redis.exists("tickers") == 0 or renew:
        return save_yahoo_finance_sp500_data_to_redis()
    else:
        pipe = redis.pipeline()
        pipe.lrange('tickers', 0, -1)
        pipe.lrange('sectors', 0, -1)
        pipe.lrange('deltas', 0, -1)
        pipe.lrange('market_caps', 0, -1)
    return pipe.execute()


# 看起來是隨機抽100個
# sp500 = sp500.sample(100)
# print(sp500)


def draw_heat_map(tickers, sectors, deltas, market_caps):
    df = pd.DataFrame({'股票代號': tickers,
                       '產業': sectors,
                       '漲跌幅': deltas,
                       '市值': market_caps,
                       })

    color_bin = [-1, -0.02, -0.01, 0, 0.01, 0.02, 1]
    df['漲跌幅'] = df['漲跌幅'].astype(float)  # 不要自己寫迴圈轉型了，用astype方便多了
    df['colors'] = pd.cut(df['漲跌幅'], bins=color_bin, labels=[
        'red', 'indianred', 'lightpink', 'lightgreen', 'lime', 'green'])
    # print(df)

    # 參考這裡吧 https://plotly.com/python/treemaps/
    fig = px.treemap(df, path=[px.Constant("all"), '產業', '股票代號'], values='市值', color='colors',
                     color_discrete_map={'(?)': '#262931', 'red': 'red', 'indianred': 'indianred',
                                         'lightpink': 'lightpink', 'lightgreen': 'lightgreen', 'lime': 'lime',
                                         'green': 'green'},

                     hover_data={'漲跌幅': ':.2p'}
                     )
    # fig.show()
    fig.write_html("./templates/stock-heatmap.html")
    print("done")


def get_ticker_list():
    redis = redisService.Redis.get_redis_connection().lrange('tickers', 0, -1)
    print(redis)


""" main方法 """
# 確認連線可用
# initialize_state_of_num_and_ticker_pairs_in_redis()
# 下一步須把所有資料取到redis內

# save_yahoo_finance_sp500_data_to_redis()
result = get_yahoo_finance_sp500_data_to_redis()
# print(type(result))
# print(type(result[0][0]))
# print(type(result[1][0]))
# print(type(result[2][0]))
# print(type(result[3][0]))
draw_heat_map(result[0], result[1], result[2], result[3])


# get_ticker_list()


""" redis list操作練習 """
# mylist=(
# 	0.021935283332769177,
# 	0.01597446793470706,
# 	0.015494427260574456
# )
# redis = get_redis_connection()
# 存值
# for i in mylist:
#     redis.lpush("mylist",i)
# 取全部
# print(redis.lrange("mylist",0,-1))
# 用key移除全部
# redis.delete("mylist")
