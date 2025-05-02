from operator import truediv
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import os
from PIL import Image
import io
import aiohttp
import random


@register("OriginiumSeal", "FengYing", "让你的头像被源石封印()", "1.0.0","https://github.com/FengYing1314/astrbot_plugin_OriginiumSeal")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 初始化时设置印章图片路径
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.seal_image_path = os.path.join(self.plugin_dir, "Sealed.png")
        if not os.path.exists(self.seal_image_path):
            logger.info(f"印章图片不存在: {self.seal_image_path}")

    # 监听所有消息事件
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def poke(self, event: AstrMessageEvent):
        '''当用户被拍一拍时，将其头像加上"封印"效果'''

        # 1. 获取原始消息对象
        raw_message = event.message_obj.raw_message
        self_id = event.get_self_id()
        group_id = event.get_group_id()
        self_id_int = int(self_id)
        group_id_int = int(group_id)

        # 2. 检测是否为拍一拍事件
        has_poke = False
        has_poke = raw_message.sub_type == 'poke'

        # 如果不是拍一拍事件，直接返回
        if not has_poke:
            return

        # 获取发送者信息,判断Poke对象是否为bot,确保是拍了bot才会触发
        target_id = raw_message.target_id
        is_poke_bot_related = str(target_id) == self_id
        if not is_poke_bot_related:
            return

        # 增加随机概率决定是否处理(后续增加配置项,暂用0.5固定概率)
        if random.random() < 0.5:
            return

        # 判断bot是否为管理员
        can_mute = False
        if event.get_platform_name()=="aiocqhttp":
            assert isinstance(event, AiocqhttpMessageEvent)
            client = event.bot
            payload = {
                "group_id": group_id_int,
                "user_id": self_id_int,
                "no_cache": True
            }
            group_info = await client.api.call_action('get_group_member_info', **payload)
            role = group_info.get("role", "member")
            if role in ["admin", "owner"]:
                can_mute = True

        try:
            sender_id = event.get_sender_id()

            # 4. 检查印章图片是否存在
            if not os.path.exists(self.seal_image_path):
                yield event.plain_result("无法处理头像: 印章图片不存在")
                return

            # 5. 获取用户头像
            avatar_url = f"https://q1.qlogo.cn/g?b=qq&nk={sender_id}&s=640"
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as response:
                    if response.status != 200:
                        yield event.plain_result(f"获取头像失败: HTTP {response.status}")
                        return
                    avatar_data = await response.read()

            # 6. 处理头像图片
            # 6.1 加载图片
            avatar_img = Image.open(io.BytesIO(avatar_data))
            seal_img = Image.open(self.seal_image_path).convert("RGBA")

            # 6.2 调整印章大小
            seal_img = seal_img.resize(avatar_img.size)

            # 6.3 设置印章透明度(70%)
            r, g, b, a = seal_img.split()
            a = a.point(lambda i: i * 0.7)
            seal_img = Image.merge('RGBA', (r, g, b, a))

            # 6.4 合成图片
            if avatar_img.mode != 'RGBA':
                avatar_img = avatar_img.convert('RGBA')
            result_img = Image.alpha_composite(avatar_img, seal_img)

            # 7. 保存处理后的图片到临时文件
            img_bytes = io.BytesIO()
            result_img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            temp_img_path = os.path.join(self.plugin_dir, f"temp_seal_{sender_id}.png")
            with open(temp_img_path, "wb") as f:
                f.write(img_bytes.getvalue())

            # 8.1 发送处理后的图片
            result = event.image_result(temp_img_path)
            yield result

            # 8.1 如果bot为管理员,可以选择禁言,60s-600s
            duration = random.randint(60, 600)
            if can_mute:
                client=event.bot
                payload = {
                        "group_id": group_id_int,
                        "user_id": sender_id,
                        "duration": duration
                    }
                await client.api.call_action('set_group_ban', **payload)
                yield event.plain_result(f"封印了 {duration},这可是没办法的呢~")
            # 9. 清理临时文件
            try:
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            except Exception:
                pass

        except Exception as e:
            logger.error(f"处理头像时出错: {str(e)}")
            yield event.plain_result(f"处理头像时出错: {str(e)}")

    async def terminate(self):
        pass