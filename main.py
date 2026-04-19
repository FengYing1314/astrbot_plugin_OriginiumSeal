import base64
import io
import os
import random
import tempfile
import time

import aiohttp
from PIL import Image as PILImage
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image as MessageImage
from astrbot.api.star import Context, Star, register
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

VERSION = "1.3.0"
AVATAR_URL_TEMPLATE = "https://q1.qlogo.cn/g?b=qq&nk={sender_id}&s=640"


@register(
    "OriginiumSeal",
    "FengYing",
    "让头像或图片被源石封印",
    VERSION,
    "https://github.com/FengYing1314/astrbot_plugin_OriginiumSeal",
)
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.seal_image_path = os.path.join(self.plugin_dir, "Sealed.png")
        if not os.path.exists(self.seal_image_path):
            logger.warning(f"印章图片不存在: {self.seal_image_path}")
        self.user_last_trigger = {}

    def _get_bool_config(self, key: str, default: bool) -> bool:
        value = self.config.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def _get_int_config(self, key: str, default: int, minimum: int = 0) -> int:
        try:
            value = int(self.config.get(key, default))
        except (TypeError, ValueError):
            value = default
        return max(minimum, value)

    def _get_float_config(
        self,
        key: str,
        default: float,
        minimum: float | None = None,
        maximum: float | None = None,
    ) -> float:
        try:
            value = float(self.config.get(key, default))
        except (TypeError, ValueError):
            value = default
        if minimum is not None:
            value = max(minimum, value)
        if maximum is not None:
            value = min(maximum, value)
        return value

    def _is_poke_enabled(self) -> bool:
        return self._get_bool_config("enable_poke_trigger", True)

    def _is_mute_enabled(self) -> bool:
        return self._get_bool_config("enable_mute", True)

    def _get_poke_cooldown_seconds(self) -> int:
        return self._get_int_config("poke_cooldown_seconds", 3600, minimum=0)

    def _get_poke_trigger_probability(self) -> float:
        return self._get_float_config(
            "poke_trigger_probability",
            0.5,
            minimum=0.0,
            maximum=1.0,
        )

    def _get_seal_opacity(self) -> float:
        return self._get_float_config("seal_opacity", 0.7, minimum=0.0, maximum=1.0)

    def _get_mute_range(self) -> tuple[int, int]:
        mute_min = self._get_int_config("mute_min_seconds", 60, minimum=0)
        mute_max = self._get_int_config("mute_max_seconds", 600, minimum=0)
        if mute_min > mute_max:
            mute_min, mute_max = mute_max, mute_min
        return mute_min, mute_max

    def _get_first_image_component(
        self, event: AstrMessageEvent
    ) -> MessageImage | None:
        for component in getattr(event.message_obj, "message", []):
            if isinstance(component, MessageImage):
                return component
        return None

    async def _download_bytes(self, url: str, error_prefix: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"{error_prefix}: HTTP {response.status}")
                return await response.read()

    async def _get_avatar_bytes(self, sender_id: str) -> bytes:
        avatar_url = AVATAR_URL_TEMPLATE.format(sender_id=sender_id)
        return await self._download_bytes(avatar_url, "获取头像失败")

    async def _get_image_component_bytes(self, image_component: MessageImage) -> bytes:
        source = image_component.url or image_component.file
        if not source:
            raise ValueError("图片消息不包含可用的地址")

        if source.startswith(("http://", "https://")):
            return await self._download_bytes(source, "获取附图失败")

        if source.startswith("file:///"):
            source = source[8:]
        elif source.startswith("base64://"):
            try:
                return base64.b64decode(source.removeprefix("base64://"))
            except Exception as exc:
                raise ValueError("图片消息的 base64 数据无效") from exc

        if os.path.exists(source):
            with open(source, "rb") as file:
                return file.read()

        raise ValueError("无法读取附图，请确认图片消息可访问")

    def _compose_sealed_image(self, image_bytes: bytes) -> PILImage.Image:
        with PILImage.open(io.BytesIO(image_bytes)) as source_image:
            base_image = source_image.convert("RGBA")
        with PILImage.open(self.seal_image_path) as seal_source:
            seal_image = seal_source.convert("RGBA")

        seal_image = seal_image.resize(base_image.size)

        opacity = self._get_seal_opacity()
        if opacity < 1.0:
            r, g, b, a = seal_image.split()
            a = a.point(lambda value: int(value * opacity))
            seal_image = PILImage.merge("RGBA", (r, g, b, a))

        return PILImage.alpha_composite(base_image, seal_image)

    def _save_temp_image(self, sender_id: str, image: PILImage.Image) -> str:
        fd, temp_img_path = tempfile.mkstemp(
            prefix=f"originium_seal_{sender_id}_",
            suffix=".png",
        )
        os.close(fd)
        image.save(temp_img_path, format="PNG")
        return temp_img_path

    async def process_image(
        self,
        sender_id: str,
        image_component: MessageImage | None = None,
    ) -> tuple[bool, str, str | None]:
        try:
            if not os.path.exists(self.seal_image_path):
                return False, "无法处理图片: 印章图片不存在", None

            if image_component is not None:
                image_bytes = await self._get_image_component_bytes(image_component)
            else:
                image_bytes = await self._get_avatar_bytes(sender_id)

            result_image = self._compose_sealed_image(image_bytes)
            try:
                temp_img_path = self._save_temp_image(sender_id, result_image)
            finally:
                result_image.close()

            return True, temp_img_path, temp_img_path
        except Exception as exc:
            logger.exception("处理图片时出错")
            return False, f"处理图片时出错: {exc}", None

    async def _cleanup_temp_image(self, temp_img_path: str | None) -> None:
        if not temp_img_path:
            return
        try:
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
        except Exception as exc:
            logger.warning(f"清理临时图片失败: {exc}")

    async def _can_mute_member(
        self,
        event: AiocqhttpMessageEvent,
        self_id_int: int,
        group_id_int: int,
        sender_id_int: int,
    ) -> bool:
        if not self._is_mute_enabled():
            return False

        try:
            client = event.bot
            self_group_info = await client.api.call_action(
                "get_group_member_info",
                user_id=self_id_int,
                group_id=group_id_int,
                no_cache=True,
            )
            sender_group_info = await client.api.call_action(
                "get_group_member_info",
                user_id=sender_id_int,
                group_id=group_id_int,
                no_cache=True,
            )
        except Exception as exc:
            logger.warning(f"群成员信息获取失败: {exc}")
            return False

        self_role = self_group_info.get("role", "member")
        sender_role = sender_group_info.get("role", "member")
        return self_role in {"admin", "owner"} and sender_role not in {
            "admin",
            "owner",
        }

    @filter.command("制作源石封印头像")
    async def seal_command(self, event: AstrMessageEvent):
        """通过 /制作源石封印头像 触发。"""
        sender_id = event.get_sender_id()
        image_component = self._get_first_image_component(event)
        success, result, temp_img_path = await self.process_image(
            sender_id,
            image_component=image_component,
        )

        try:
            if success:
                yield event.image_result(result)
            else:
                yield event.plain_result(result)
        finally:
            await self._cleanup_temp_image(temp_img_path)

    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def poke(self, event: AstrMessageEvent):
        """当用户拍一拍 bot 时，将其头像加上封印效果。"""
        if not self._is_poke_enabled():
            return

        if not isinstance(event, AiocqhttpMessageEvent):
            return

        raw_message = getattr(event.message_obj, "raw_message", None)
        if raw_message is None or getattr(raw_message, "sub_type", None) != "poke":
            return

        self_id = event.get_self_id()
        group_id = event.get_group_id()
        sender_id = event.get_sender_id()

        if str(getattr(raw_message, "target_id", "")) != str(self_id):
            return

        try:
            self_id_int = int(self_id)
            group_id_int = int(group_id)
            sender_id_int = int(sender_id)
        except (TypeError, ValueError):
            logger.warning(f"非 QQ 号跳过处理: {sender_id}")
            return

        current_time = time.time()
        last_trigger_time = self.user_last_trigger.get(sender_id)
        cooldown_seconds = self._get_poke_cooldown_seconds()
        if (
            last_trigger_time is not None
            and current_time - last_trigger_time < cooldown_seconds
        ):
            return

        probability = self._get_poke_trigger_probability()
        if probability <= 0 or random.random() > probability:
            return

        self.user_last_trigger[sender_id] = current_time
        can_mute = await self._can_mute_member(
            event,
            self_id_int,
            group_id_int,
            sender_id_int,
        )

        success, result, temp_img_path = await self.process_image(sender_id)
        try:
            if not success:
                yield event.plain_result(result)
                return

            yield event.image_result(result)

            if can_mute:
                mute_min, mute_max = self._get_mute_range()
                duration = random.randint(mute_min, mute_max)
                try:
                    await event.bot.api.call_action(
                        "set_group_ban",
                        group_id=group_id_int,
                        user_id=sender_id_int,
                        duration=duration,
                    )
                    yield event.plain_result(f"封印了 {duration}s,这可是没办法的呢~")
                except Exception as exc:
                    logger.warning(f"禁言失败: {exc}")
        finally:
            await self._cleanup_temp_image(temp_img_path)

    async def terminate(self):
        pass
