<<<<<<< HEAD
=======
import io
import os
import random

import aiohttp
from PIL import Image
from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent


@register("OriginiumSeal", "FengYing", "让你的头像被源石封印()", "1.2.0","https://github.com/FengYing1314/astrbot_plugin_OriginiumSeal")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 初始化时设置印章图片路径
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
>>>>>>> 008cd46 (重建一下git)
        self.seal_image_path = os.path.join(self.plugin_dir, "Sealed.png")
