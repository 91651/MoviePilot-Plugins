from typing import Any, List, Dict, Tuple, Optional, Union

from app.chain.download import DownloadChain
from app.chain.media import MediaChain
from app.core.event import eventmanager
from app.core.metainfo import MetaInfo
from app.db.downloadhistory_oper import DownloadHistoryOper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType, TransferTorrent, DownloadingTorrent
from app.schemas.types import EventType, TorrentStatus, MessageChannel
from app.utils.string import StringUtils


class StartDownloadNotification(_PluginBase):
    # 插件名称
    plugin_name = "开始下载通知"
    # 插件描述
    plugin_desc = "下载任务开始时，通知推送给配置的渠道，支持消息隔离。"
    # 插件图标
    plugin_icon = "downloadmsg.png"
    # 插件版本
    plugin_version = "1.1"
    # 插件作者
    plugin_author = "91651"
    # 作者主页
    author_url = "https://github.com/91651"
    # 插件配置项ID前缀
    plugin_config_prefix = "startdownloadnotification_"
    # 加载顺序
    plugin_order = 22
    # 可使用的用户级别
    auth_level = 2

    # 私有属性
    _enabled = False
    _type = None
    _adminuser = None
    _downloadhis = None

    def init_plugin(self, config: dict = None):
        self._downloadhis = DownloadHistoryOper()
        # 停止现有任务
        self.stop_service()

        if config:
            self._enabled = config.get("enabled")
            self._type = config.get("type") or 'admin'
            self._adminuser = config.get("adminuser")

    @eventmanager.register(EventType.NoticeMessage)
    def startdownload(self, event):
        """
        资源开始下载时推送通知
        """
        data = event.event_data
        logger.info(f"开始下载通知--消息: {data['type']}")

        if data['type'] != NotificationType.Download and data['source'] != self:
            return
        logger.info(self)
        logger.info(data)

        # 推送管理员
        if self._type == "admin" or self._type == "both":
            if not self._adminuser:
                logger.error("未配置管理员用户")
                return

            logger.info("推送消息给管理员")
            for username in str(self._adminuser).split(","):
                self.__send_msg(data=data, username=username)


        # 尝试推送给渠道用户
        if self._type == "user" or self._type == "both":
            # 如果用户是管理员，无需重复推送
                if (self._type == "admin" or self._type == "both") and self._adminuser and username in str(
                        self._adminuser).split(","):
                    return
                
                logger.info("尝试推送给渠道用户")
                self.__send_msg(data=data,
                                username=data['username'])

        if self._type == "all":
            logger.info("推送消息给所有人")
            self.__send_msg(data=data)

    def __send_msg(self, data, username: str = None):
        """
        发送消息
        """
        channel_value = None
        title = data['title']
        source = self
        messages = []
        image = data['image']
        

        # 用户消息渠道
        if channel_value:
            channel = next(
                (channel for channel in MessageChannel.__members__.values() if channel.value == channel_value), None)
        else:
            channel = None
        
        logger.info(f"开始推送消息--渠道: {channel}，用户: {username}")
        self.post_message(mtype=NotificationType.Download,
                          channel=channel,
                          source = source,
                          title=title,
                          text="测试",
                          userid=username)

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
                   {
                       'component': 'VForm',
                       'content': [
                           {
                               'component': 'VRow',
                               'content': [
                                   {
                                       'component': 'VCol',
                                       'props': {
                                           'cols': 12
                                       },
                                       'content': [
                                           {
                                               'component': 'VSwitch',
                                               'props': {
                                                   'model': 'enabled',
                                                   'label': '启用插件',
                                               }
                                           }
                                       ]
                                   }
                               ]
                           },
                           {
                               'component': 'VRow',
                               'content': [
                                   {
                                       'component': 'VCol',
                                       'props': {
                                           'cols': 12
                                       },
                                       'content': [
                                           {
                                               'component': 'VTextField',
                                               'props': {
                                                   'model': 'adminuser',
                                                   'label': '管理员用户',
                                                   'placeholder': '多个用户,分割'
                                               }
                                           }
                                       ]
                                   }
                               ]
                           },
                           {
                               'component': 'VRow',
                               'content': [
                                   {
                                       'component': 'VCol',
                                       'props': {
                                           'cols': 12
                                       },
                                       'content': [
                                           {
                                               'component': 'VSelect',
                                               'props': {
                                                   'model': 'type',
                                                   'label': '推送类型',
                                                   'items': [
                                                       {'title': '管理员', 'value': 'admin'},
                                                       {'title': '下载用户', 'value': 'user'},
                                                       {'title': '管理员和下载用户', 'value': 'both'},
                                                       {'title': '所有用户', 'value': 'all'}
                                                   ]
                                               }
                                           }
                                       ]
                                   }
                               ]
                           }
                       ]
                   }
               ], {
                   "enabled": False,
                   "adminuser": "",
                   "type": "admin"
               }

    def get_page(self) -> List[dict]:
        pass

    def stop_service(self):
        pass
