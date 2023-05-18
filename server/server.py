# -*- coding:utf-8 -*-

import logging
import asyncio
import threading

from dotenv import load_dotenv

load_dotenv()

from sanic import Sanic

from recite.views import asr_view, tts_view, pivot_view, tts_speech_view
from recite.settings import EBROSE_LOGGER_CONFIG
from recite.cache_build import CacheBuilder

# 设置 log 
logging.config.dictConfig(EBROSE_LOGGER_CONFIG)

app = Sanic(name='recite')

app.add_route(asr_view, '/ebrose/asr', methods=["POST"])
app.add_route(tts_view, '/ebrose/tts', methods=["POST"])
app.add_route(pivot_view, '/ebrose/pivot', methods=["GET"])
app.add_route(tts_speech_view, "/ebrose/speech", methods=["GET"])


# 启动定时任务
class CacheBuilderObject(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)

    def run(self) -> None:
        cachebuilder = CacheBuilder()
        asyncio.run(cachebuilder.runner())



if __name__ == "__main__":
    obj = CacheBuilderObject()
    obj.start()
    app.run(host="0.0.0.0", port=8000, debug=True, verbosity=True, access_log=True)
