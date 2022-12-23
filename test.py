# pip install pandas yfinance plotly

""" 
這裡要繪製的是market heatmap，因為要去yahoo finance取500筆資料，
所以我們一天存一次到Redis內，每次使用者訪問的時候去redis拿資料就好。
資料更新的部分，觸發點可以設計在每日job跟強制更新按鈕(按鈕前後端都要debounce)
"""
from dotenv import load_dotenv
import plotly.express as px
import pandas as pd
import yfinance as yf
import redis
import os
import pickle
import json

""" redis連線 """
load_dotenv()
REDIS_HOST=os.getenv('REDIS_HOST') 
REDIS_PORT=os.getenv('REDIS_PORT')
REDIS_PASSWORD=os.getenv('REDIS_PASSWORD')

def get_redis_connection():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT,
                       password=REDIS_PASSWORD, charset="utf-8", decode_responses=True)


def initialize_state_of_num_and_ticker_pairs_in_redis():
    conn = get_redis_connection()
    conn.zadd("ETORO_DICT_KEY_NAME", {"member": 999})
    # 最終結構是etoroDict(zset)內有4845條類似111:1,EURUSD的結構
    print('reset redis by job')
    return


""" 存資料到redis """


def save_yahoo_finance_sp500_data_to_redis():
    sp500 = pd.read_html(
        r'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol']

    tickers = []
    deltas = []
    sectors = []
    market_caps = []

    # for ticker in sp500:
    for ticker in ['MSFT','ABMD']:

        # try:
            # create Ticker object
            stock = yf.Ticker(ticker)
            # print(vars(stock))#物件結構如下，
            # 因為有非python原生的數據類型(倒數2到6項)，所以不能直接用pickle.dump()
            # {'ticker': 'ABBV', 'session': None, '_history': None, '_history_metadata': None, '_base_url': 'https://query2.finance.yahoo.com', '_scrape_url': 'https://finance.yahoo.com/quote', '_tz': None, '_isin': None, '_news': [], '_shares': None, '_earnings_dates': {}, '_earnings': None, '_financials': None, '_data': <yfinance.data.TickerData object at 0x0000020C8D5C9450>, '_analysis': <yfinance.scrapers.analysis.Analysis object at 0x0000020C8D5C94E0>, '_holders': <yfinance.scrapers.holders.Holders object at 0x0000020C8D5C8700>, '_quote': <yfinance.scrapers.quote.Quote object at 0x0000020C8D7D7850>, '_fundamentals': <yfinance.scrapers.fundamentals.Fundamentals object at 0x0000020C8D7D7A30>, '_expirations': {}}

            tickers.append(ticker)

            # download info
            info = stock.info
            # download sector
            sectors.append(info['sector'])

            # download daily stock prices for 2 days
            hist = stock.history('2d')


            # print(hist.columns.values.tolist())
            # ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
            print(len(hist['Close']))
            print(hist['Close'])

            # 印出來長這樣，所以不知道為什麼他就只有一筆，這樣的話就還是不要用list比較好，或是要有交易的概念了
            # 2
            # Date
            # 2022 - 12 - 21    00: 00:00 - 05: 00
            # 244.429993
            # 2022 - 12 - 22    00: 00:00 - 05: 00
            # 235.320007
            # Name: Close, dtype: float64
            # downloaded    MSFT
            # 1
            # Date
            # 2022 - 12 - 21    00: 00:00 - 05: 00
            # 381.019989
            # Name: Close, dtype: float64

            # calculate change in stock price (from a trading day ago)
            deltas.append((hist['Close'][1] - hist['Close'][0]) / hist['Close'][0])

            # calculate market cap
            market_caps.append(info['sharesOutstanding'] * info['previousClose'])

            # add print statement to ensure code is running
            print(f'downloaded {ticker}')

        # except Exception as e:
        #     print(f'downloaded {ticker} failed')
        #     print(e)

    # 存成list就不需要json了ˊ
    # tickers_list = json.dumps(tickers)
    # deltas_list = json.dumps(deltas)
    # sectors_list = json.dumps(sectors)    
    # market_caps_list = json.dumps(market_caps)

    tickers_list = tickers
    deltas_list = deltas
    sectors_list = sectors
    market_caps_list = market_caps

    conn = get_redis_connection()
    pipe = conn.pipeline()
    pipe.delete("tickers")
    pipe.delete("deltas")
    pipe.delete("sectors")
    pipe.delete("market_caps")

    for i in range(0, len(tickers_list)):
        # print(tickers_list[i])
        pipe.rpush('tickers', tickers_list[i])
        pipe.rpush('deltas', deltas_list[i])
        pipe.rpush('sectors', sectors_list[i])
        pipe.rpush('market_caps', market_caps_list[i])
    pipe.execute()

    return tickers_list, deltas_list, sectors_list, market_caps_list


""" 取資料 """


def get_yahoo_finance_sp500_data_to_redis():
    conn = get_redis_connection()
    if conn.exists("tickers") == 0:
        return save_yahoo_finance_sp500_data_to_redis()
    else:
        pipe = conn.pipeline()
        pipe.get('tickers')
        pipe.get('deltas')
        pipe.get('sectors')
        pipe.get('market_caps')
    return pipe.execute()


# 看起來是隨機抽100個
# sp500 = sp500.sample(100)
# print(sp500)


# df = pd.DataFrame({'ticker': tickers,
#                   'sector': sectors,
#                    'delta': deltas,
#                    'market_cap': market_caps,
#                    })
# 
# color_bin = [-1, -0.02, -0.01, 0, 0.01, 0.02, 1]
# df['colors'] = pd.cut(df['delta'], bins=color_bin, labels=[
#                       'red', 'indianred', 'lightpink', 'lightgreen', 'lime', 'green'])
# # print(df)
# 
# fig = px.treemap(df, path=[px.Constant("all"), 'sector', 'ticker'], values='market_cap', color='colors',
#                  color_discrete_map={'(?)': '#262931', 'red': 'red', 'indianred': 'indianred',
#                                      'lightpink': 'lightpink', 'lightgreen': 'lightgreen', 'lime': 'lime', 'green': 'green'},
# 
#                  hover_data={'delta': ':.2p'}
#                  )
# # fig.show()


""" main方法 """
# 確認連線可用
# initialize_state_of_num_and_ticker_pairs_in_redis()
# 下一步須把所有資料取到redis內

save_yahoo_finance_sp500_data_to_redis()
# result=get_yahoo_finance_sp500_data_to_redis()
# print(type(result))
# print(result[0])


# redis list操作練習
# mylist=(
# 	0.021935283332769177,
# 	0.01597446793470706,
# 	0.015494427260574456
# )
# conn = get_redis_connection()
# 存值
# for i in mylist:
#     conn.lpush("mylist",i)
# 取全部
# print(conn.lrange("mylist",0,-1))
# 用key移除全部
# conn.delete("mylist")
