import redisService
import threading
import whatCanTradeToday
import sendPhotoByTelegram

conn = redisService.Redis.get_redis_connection()


def job_in_master():
    mySendList = []
    remaining = len(redisService.Redis.get_member_in_initial_state(redisService.ETORO_DICT_KEY_NAME))
    # print(remaining)
    while remaining > 0:
        threads = []
        for i in range(5):  # 五條(太多條會429 too many request)
            # 啟動執行續前取出要執行的ticker，並在啟動下一條執行續前把狀態從未取用(111)改成已取用(999)，避免重複取
            num_ticker = redisService.Redis.change_state_of_num_and_ticker_pairs_in_redis_when_finish_in_lua()
            # 啟動執行續，處理csv
            threads.append(threading.Thread(name=f'{i}', target=job_unit_csv_module, args=(num_ticker, str(i), 3)))
            threads[i].start()
        # 五條都做完再做下一批
        for i in range(5):
            threads[i].join()

        mySet = redisService.Redis.get_watchListToday_in_redis()
        mySendList += list(mySet)
        job_unit_plot_module(mySet)  # 一張一張圖處理，因為線程不安全
        print("Done and Plotting the following list")
        print(mySet)
        remaining = len(redisService.Redis.get_member_in_initial_state(redisService.ETORO_DICT_KEY_NAME))
    # 送圖也一個一個request送，送完可以再修成異部請求
    for i in mySendList:
        try:
            sendPhotoByTelegram.main(i)
        except Exception as e:
            pass


def job_in_slave():
    ticker = ['27', '28', '29', '1002', '1003', '18', '3025', '3246', '3163', '3306',
              '4465', '4459', '3008', '1467', '45', '63', '1111', '3006', '1951',
              '5968', '1588', '93', '6357', '3024', '3019', '4269', '3004', '1118',
              '2316', '4463', '4251', '100000']

    nameList = ['spx500', 'nsdq100', 'dj30', 'goog', 'fb', 'gold', 'gld', 'uvxy', 'vix',
                'qqq', 'tqqq', 'sqqq', 'xle', 'gs', 'usd_cnh', 'usd_mxn', 'tsla', 'ma',
                'swn', 'tdoc', 'x', 'cotton', 'smh', 'xly', 'xli', 'iwd', 'xlf', 'brk_b',
                '2318_hk', 'soxx', 'isrg', 'btc']

    # ['27,spx500', '28,nsdq100', '29,dj30', '1002,goog', '1003,fb', '18,gold', '3025,gld', '3246,uvxy', '3163,vix',
    #  '3306,qqq', '4465,tqqq', '4459,sqqq', '3008,xle', '1467,gs', '45,usd_cnh', '63,usd_mxn', '1111,tsla', '3006,ma',
    #  '1951,swn', '5968,tdoc', '1588,x', '93,cotton', '6357,smh', '3024,xly', '3019,xli', '4269,iwd', '3004,xlf',
    #  '1118,brk_b', '2316,2318_hk', '4463,soxx', '4251,isrg', '100000,btc']

    myList = list()
    for i, j in zip(ticker, nameList):
        items = str(i) + ',' + str(j)
        myList.append(items)

    job_unit(myList, bb_range=2)


def job_in_test():
    ticker = ['1951']
    nameList = ['swn']
    # ['27,spx500', '28,nsdq100', '29,dj30', '1002,goog', '1003,fb', '18,gold', '3025,gld', '3246,uvxy', '3163,vix',
    #  '3306,qqq', '4465,tqqq', '4459,sqqq', '3008,xle', '1467,gs', '45,usd_cnh', '63,usd_mxn', '1111,tsla', '3006,ma',
    #  '1951,swn', '5968,tdoc', '1588,x', '93,cotton', '6357,smh', '3024,xly', '3019,xli', '4269,iwd', '3004,xlf',
    #  '1118,brk_b', '2316,2318_hk', '4463,soxx', '4251,isrg', '100000,btc']
    myList = list()
    for i, j in zip(ticker, nameList):
        items = str(i) + ',' + str(j)
        myList.append(items)
    job_unit(myList, bb_range=1)


def job_unit(num_ticker, thread_number: str = "", bb_range=2):
    watchListToday = whatCanTradeToday.singleton_main(num_ticker, thread_number, bb_range)
    for i in watchListToday:
        try:
            sendPhotoByTelegram.main(i)
        except Exception as e:
            print(e)


def job_unit_csv_module(num_ticker, thread_number: str = "", bb_range=3):
    watchListToday = []
    ticker, nameList = whatCanTradeToday.make_num_ticker_list(num_ticker)
    for i in range(len(nameList)):
        result = whatCanTradeToday.singleton_bb_csv_module(nameList[i], ticker[i], thread_number, bb_range)
        if result:
            watchListToday.append(nameList[i])
    redisService.Redis.add_watchListToday_in_redis(watchListToday)


def job_unit_plot_module(ticker_name_set):
    watchListToday = []
    for i in ticker_name_set:
        # print(i)
        result = whatCanTradeToday.singleton_bb_plot_module(i)
        if result:
            watchListToday.append(i)
        redisService.Redis.delete_watchListToday_element_in_redis(i)
    return watchListToday
