#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import threading
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
from flask import render_template
import logging
from time import strftime
from logging.config import dictConfig
import os
import redisService
from redisService import Redis
import jobService
from dotenv import load_dotenv
from redis import Redis as rs
import time


# 不加這行，整個系統都讀不到環境變數
load_dotenv()


tw = pytz.timezone('Asia/Taipei')
now = datetime.now(tw)

sched = BackgroundScheduler(timezone="Asia/Taipei", daemon=True)
# # 正式用如下
if os.getenv('ENVIRONMENT')=='master':
    sched.add_job(jobService.job_in_master, 'cron', day_of_week='mon-fri', hour='21,4', minute=31)
elif os.getenv('ENVIRONMENT')=='slave':
    sched.add_job(jobService.job_in_slave, 'cron', day_of_week='mon-fri', hour='21,4', minute=31)
sched.add_job(Redis.initialize_state_of_num_and_ticker_pairs_in_redis, 'cron', day_of_week='mon-fri', hour='19,23', minute=59, id='my_job_re')

# 測試用如下
# sched.add_job(jobService.job_in_master, 'cron', day_of_week='mon-fri',hour='16,21,22,4', minute=35, id='my_job_test')
# sched.add_job(Redis.initialize_state_of_num_and_ticker_pairs_in_redis, 'cron', day_of_week='mon-fri', hour='16,19,23', minute=59, id='my_job_re')


sched.start()

app = Flask(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))

#Heroku會找不到log存的位置，可能沒權限或沒給空間建
if os.getenv('DEPLOY_SITE')!='heroku':
    dictConfig = {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s | %(module)s >>> %(message)s",
                "datefmt": "%B %d, %Y %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": f'{dir_path}\\flask.log',
                "formatter": "default",
            },
        },
        "loggers": {
            "console_logger": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "file_logger": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False,
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console", "file"]},
    }

    logging.config.dictConfig(dictConfig)
    logger = logging.getLogger("file")
    logger.info('info message')
else:
    dictConfig={}

# # 註冊一個函數，如果沒有未處理的異常拋出，在每次請求之後執行
# @app.after_request
# def after_request(response):
#     timestamp = strftime('[%Y-%b-%d %H:%M]')
#     ##有dictConfig後就都不需要這些app.logger了
#     app.logger.info('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme,
#                     request.full_path, response.status)
#     print('after request finished:' + request.url)
#     response.headers['key'] = 'value'
#     return response


@app.route('/')
def hello_world():
    return render_template('panel.html', system_datetime=datetime.now(), taipei_datetime=datetime.now(tw))


@app.route('/tool',methods=['GET'])
def sent_manually():
    environment = request.values.get('env')
    print(environment)
    if environment=='master':
        jobService.job_in_master()
    elif environment=='slave':
        jobService.job_in_slave()
    return "images sent"


@app.route('/tool-test',methods=['GET'])
def sent_manually_test():
    jobService.job_in_test()
    return "images sent"


@app.route('/log')
def show_log():
    text = ""
    with open(dir_path + "\\flask.log", mode="r") as log:
        # text=log
        for i in log.readlines():
            # print(i)
            # print(type(i))
            text += i
            text += '<br>'
    return text


@app.route('/re')
def initialize_state_of_num_and_ticker_pairs_in_redis():
    Redis.initialize_state_of_num_and_ticker_pairs_in_redis()
    return 'done'


@app.route('/redis-test')
def redis_connection_test():
    conn=Redis.get_redis_connection()
    return f'ping is {conn.ping()}'


@app.route('/redis-set')
def redis_set_test():
    redisService.Redis.add_watchListToday_in_redis(['aaa', 'bbb'])
    mySet = redisService.Redis.get_watchListToday_in_redis()
    print(mySet)
    for i in ['aaa', 'bbb']:
        redisService.Redis.delete_watchListToday_element_in_redis(i)
    mySet = redisService.Redis.get_watchListToday_in_redis()
    print(mySet)
    return "done"


@app.route('/lua-test')
def redis_lua_test():
    redis = redisService.Redis.get_redis_connection()
    script="""
    local key = KEYS[1]
    local seconds = ARGV[1]
    local value = ARGV[2]
    redis.call('SETEX',key,seconds,value)
    return redis.call('GET',key)    
    """
    cmd = redis.register_script(script)
    result = cmd(keys=['key'],args=[100,'value'])
    return f'done and return {result}'


@app.route('/status-non-lua-test1')
def redis_status_non_lua_test1():
    time_start = time.time() #開始計時
    for i in range(100):
        num_ticker = redisService.Redis.get_member_in_initial_state(redisService.ETORO_DICT_KEY_NAME)
        for ticker in num_ticker:
            redisService.Redis.change_state_of_num_and_ticker_pairs_in_redis_when_finish(ticker)
    time_end = time.time()    #結束計時
    time_c= time_end - time_start   #執行所花時間
    return f'done in {time_c}' #~300s


@app.route('/status-non-lua-test2')
def redis_status_non_lua_test2():
    time_start = time.time() #開始計時
    conn = redisService.Redis.get_redis_connection()
    for i in range(100):
        myList = conn.zrangebyscore(redisService.ETORO_DICT_KEY_NAME, '100', '120', start=0, num=100)
        for member in myList:
            conn.zadd(redisService.ETORO_DICT_KEY_NAME, {member: 999})
    time_end = time.time()    #結束計時
    time_c= time_end - time_start   #執行所花時間
    return f'done in {time_c}' #46s~91s


@app.route('/status-lua-test')
def redis_status_lua_test():
    time_start = time.time() #開始計時
    my_count=0
    for i in range(100):
        result=redisService.Redis.change_state_of_num_and_ticker_pairs_in_redis_when_finish_in_lua()
        my_count+=len(result)
    time_end = time.time()    #結束計時
    time_c= time_end - time_start   #執行所花時間
    return f'done {my_count} in {time_c}' #1s~5s 快又穩，又保證原子性


if __name__ == '__main__':
    # # 記log
    # handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=3)
    # app.logger = logging.getLogger('tdm')
    # app.logger.setLevel(logging.ERROR)
    # app.logger.addHandler(handler)

    # flask重啟時會有兩條執行續，不能讓他們都跑，不然會有兩張圖(use_reloader=False)
    # app.run(debug=True, use_reloader=False)
    # app.run(debug=False, port=os.getenv("PORT", default=5000))
    app.run(use_reloader=False, debug=False,
            port=os.getenv("PORT", default=8000))
    # app.run(debug=True, port=os.getenv("PORT", default=5000))

# linux執行，
    # 3 process，背景執行，自動重載
    # gunicorn3 --workers=3 app:app --daemon --reload
    # pkill gunicorn
    # 砍掉當前所有進程
# vscode執行
    #python -m flask run
