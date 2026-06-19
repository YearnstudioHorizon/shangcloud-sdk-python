from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client

from .models import MMOJoinRoomResponse, MMONewRoomResponse, UserBasicInfo


class User(ABC):
    @abstractmethod
    def init_user(self, access_token: str, refresh_token: str, token_type: str,
                  expires_in: int, client: Client) -> None:
        pass

    @abstractmethod
    def save(self) -> None:
        pass

    @abstractmethod
    def is_expired(self) -> bool:
        pass

    @abstractmethod
    def get_basic_info(self) -> UserBasicInfo:
        pass

    @abstractmethod
    def get_variable(self, key: str) -> str:
        pass

    @abstractmethod
    def set_variable(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def delete_variable(self, key: str) -> None:
        pass


class UserInstance(User):
    def __init__(self) -> None:
        self._access_token: str = ""
        self._refresh_token: str = ""
        self._token_type: str = ""
        self.expires_in: int = 0
        self.expiry_time: datetime = datetime.now()
        self._client: Client | None = None

    def init_user(self, access_token: str, refresh_token: str, token_type: str,
                  expires_in: int, client: Client) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_type = token_type
        self.expires_in = expires_in
        self._client = client
        self.expiry_time = datetime.now() + timedelta(seconds=expires_in)
        self.save()

    def save(self) -> None:
        pass

    def is_expired(self) -> bool:
        return datetime.now() + timedelta(seconds=60) > self.expiry_time

    def get_basic_info(self) -> UserBasicInfo:
        return self._client._get_user_basic_info(self._access_token, self._token_type)

    def get_variable(self, key: str) -> str:
        return self._client._variable_action(
            "read", key, "", self._access_token, self._token_type
        )

    def set_variable(self, key: str, value: str) -> None:
        self._client._variable_action(
            "write", key, value, self._access_token, self._token_type
        )

    def delete_variable(self, key: str) -> None:
        self._client._variable_action(
            "delete", key, "", self._access_token, self._token_type
        )

    def new_room(self, protocol: str = "") -> MMONewRoomResponse:
        return self._client.mmo_new_room(self._access_token, self._token_type, protocol)

    def join_room(self, room_id: str, protocol: str = "") -> MMOJoinRoomResponse:
        return self._client.mmo_join_room(self._access_token, self._token_type, room_id, protocol)

    def set_room_config(self, room_id: str, allow_multi_login: bool) -> None:
        self._client.mmo_set_room_config(self._access_token, self._token_type, room_id, allow_multi_login)

    def set_room_data(self, room_id: str, key: str, value, data_type: str = "") -> None:
        self._client.mmo_set_room_data(self._access_token, self._token_type, room_id, key, value, data_type)

    def get_room_data(self, room_id: str) -> dict:
        return self._client.mmo_get_room_data(self._access_token, self._token_type, room_id)

    def delete_room_data(self, room_id: str, key: str) -> None:
        self._client.mmo_delete_room_data(self._access_token, self._token_type, room_id, key)

    def kick_user(self, room_id: str, target_uid: str) -> None:
        self._client.mmo_kick_user(self._access_token, self._token_type, room_id, target_uid)

    def get_room_user_count(self, room_id: str) -> int:
        return self._client.mmo_get_room_user_count(self._access_token, self._token_type, room_id)
