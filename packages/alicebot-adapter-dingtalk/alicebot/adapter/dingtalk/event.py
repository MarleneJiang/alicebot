"""DingTalk 适配器事件。"""
import time
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, List, Union, Literal, Optional

from pydantic import Field, BaseModel

from alicebot.event import MessageEvent

from .message import DingTalkMessage
from .exceptions import WebhookExpiredError

if TYPE_CHECKING:
    from . import DingTalkAdapter


class UserInfo(BaseModel):
    dingtalkId: str
    staffId: Optional[str]


class Text(BaseModel):
    content: str


class DingTalkEvent(MessageEvent["DingTalkAdapter", DingTalkMessage]):
    """DingTalk 事件基类"""

    type: Optional[str] = Field(alias="msgtype")

    msgtype: str
    msgId: str
    createAt: str
    conversationType: Literal["1", "2"]
    conversationId: str
    conversationTitle: Optional[str]
    senderId: str
    senderNick: str
    senderCorpId: Optional[str]
    sessionWebhook: str
    sessionWebhookExpiredTime: int
    isAdmin: Optional[bool]
    chatbotCorpId: Optional[str]
    isInAtList: Optional[bool]
    senderStaffId: Optional[str]
    chatbotUserId: str
    atUsers: List[UserInfo]
    text: Text

    response_msg: Union[None, str, Dict[str, Any], DingTalkMessage] = None
    response_at: Union[None, Dict[str, Any], DingTalkMessage] = None

    @cached_property
    def message(self) -> DingTalkMessage:
        return DingTalkMessage.text(self.text.content)

    def get_plain_text(self) -> str:
        """获取消息的纯文本内容。

        Returns:
            消息的纯文本内容。
        """
        return self.message.get_plain_text()

    async def reply(
        self,
        message: Union[str, Dict[str, Any], DingTalkMessage],
        at: Union[None, Dict[str, Any], DingTalkMessage] = None,
    ) -> Dict[str, Any]:
        """回复消息。

        Args:
            message: 回复消息的内容，可以是 `str`, `Dict` 或 `DingTalkMessage`。
            at: 回复消息时 At 的对象，必须时 at 类型的 `DingTalkMessage`，或者符合标准的 `Dict`。

        Returns:
            调用 Webhook 地址后钉钉服务器的响应。

        Raises:
            WebhookExpiredError: 当前事件的 Webhook 地址已经过期。
            ...: 同 `DingTalkAdapter.send()` 方法。
        """
        if self.sessionWebhookExpiredTime > time.time() * 1000:
            return await self.adapter.send(
                webhook=self.sessionWebhook,
                conversation_type=self.conversationType,
                msg=message,
                at=at,
            )
        else:
            raise WebhookExpiredError
